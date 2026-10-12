export interface HarnessStep {
  stdin: string
  timeoutSeconds: number
  expectedStdout?: string
  expectedFiles?: Record<string, string>
}

export interface HarnessCase {
  name: string
  files?: Record<string, string>
  steps: HarnessStep[]
}

export interface HarnessConfig {
  source: string
  cases: HarnessCase[]
  collectFiles?: boolean
}

const encoder = new TextEncoder()

function base64(value: string): string {
  const bytes = encoder.encode(value)
  let binary = ''
  for (let index = 0; index < bytes.length; index += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(index, index + 0x8000))
  }
  return btoa(binary)
}

function protocol(config: HarnessConfig): string {
  const lines = [base64(config.source), String(config.cases.length), config.collectFiles ? '1' : '0']
  for (const testCase of config.cases) {
    lines.push(base64(testCase.name))
    const initialFiles = Object.entries(testCase.files ?? {})
    lines.push(String(initialFiles.length))
    for (const [name, content] of initialFiles) lines.push(base64(name), base64(content))
    lines.push(String(testCase.steps.length))
    for (const step of testCase.steps) {
      lines.push(base64(step.stdin), String(Math.max(1, Math.ceil(step.timeoutSeconds))))
      lines.push(step.expectedStdout === undefined ? '0' : '1', base64(step.expectedStdout ?? ''))
      const expectedFiles = Object.entries(step.expectedFiles ?? {})
      lines.push(String(expectedFiles.length))
      for (const [name, content] of expectedFiles) lines.push(base64(name), base64(content))
    }
  }
  return base64(lines.join('\n'))
}

const JAVA_HARNESS = String.raw`
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.stream.Stream;
import javax.tools.ToolProvider;

public class Main {
  private static final String CONFIG = "__CONFIG__";
  private static final int OUTPUT_LIMIT = 16000;
  private static String line(BufferedReader reader) throws IOException {
    String value = reader.readLine();
    if (value == null) throw new EOFException("Incomplete execution request.");
    return value;
  }
  private static String decoded(BufferedReader reader) throws IOException {
    return new String(Base64.getDecoder().decode(line(reader)), StandardCharsets.UTF_8);
  }
  private static String quote(String value) {
    StringBuilder result = new StringBuilder("\"");
    for (int index = 0; index < value.length(); index++) {
      char ch = value.charAt(index);
      switch (ch) {
        case '"': result.append("\\\""); break;
        case '\\': result.append("\\\\"); break;
        case '\b': result.append("\\b"); break;
        case '\f': result.append("\\f"); break;
        case '\n': result.append("\\n"); break;
        case '\r': result.append("\\r"); break;
        case '\t': result.append("\\t"); break;
        default:
          if (ch < 0x20) result.append(String.format("\\u%04x", (int)ch));
          else result.append(ch);
      }
    }
    return result.append('"').toString();
  }
  private static boolean safeName(String name) {
    return name.matches("[A-Za-z0-9][A-Za-z0-9_.-]{0,79}")
      && !name.endsWith(".") && !name.equalsIgnoreCase("Main.java")
      && !name.toLowerCase(Locale.ROOT).endsWith(".class")
      && !name.matches("(?i)^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\\..*)?$");
  }
  private static String normalize(String value) {
    return value.replace("\r\n", "\n").replaceFirst("\\n$", "");
  }
  private static final class Capture extends Thread {
    private final InputStream input;
    private final ByteArrayOutputStream data = new ByteArrayOutputStream();
    private boolean truncated;
    Capture(InputStream input) { this.input = input; setDaemon(true); }
    @Override public void run() {
      byte[] chunk = new byte[4096];
      try (InputStream stream = input) {
        int read;
        while ((read = stream.read(chunk)) >= 0) {
          int room = OUTPUT_LIMIT - data.size();
          if (room > 0) data.write(chunk, 0, Math.min(room, read));
          if (read > room) truncated = true;
        }
      } catch (IOException ignored) {}
    }
    String text() { return data.toString(StandardCharsets.UTF_8); }
  }
  private static final class StepResult {
    String status, stdout, stderr;
    Integer exitCode;
    boolean timedOut, truncated;
    List<String[]> fileChecks = new ArrayList<>();
  }
  private static void removeTree(Path root) throws IOException {
    if (!Files.exists(root, LinkOption.NOFOLLOW_LINKS)) return;
    try (Stream<Path> paths = Files.walk(root)) {
      paths.sorted(Comparator.reverseOrder()).forEach(path -> {
        try { Files.deleteIfExists(path); } catch (IOException ignored) {}
      });
    }
  }
  private static StepResult execute(Path classes, Path folder, String stdin, int timeout,
                                    Map<String, String> expectedFiles) throws Exception {
    Path java = Path.of(System.getProperty("java.home"), "bin", "java");
    ProcessBuilder builder = new ProcessBuilder(java.toString(), "-Xmx128m", "-XX:+UseSerialGC",
      "-Dfile.encoding=UTF-8", "-cp", classes.toString(), "Main");
    builder.directory(folder.toFile());
    Map<String, String> env = builder.environment();
    String path = env.get("PATH");
    env.clear();
    if (path != null) env.put("PATH", path);
    env.put("LANG", "C.UTF-8");
    env.put("HOME", folder.toString());
    builder.redirectErrorStream(false);
    long started = System.nanoTime();
    Process process = builder.start();
    Capture stdout = new Capture(process.getInputStream());
    Capture stderr = new Capture(process.getErrorStream());
    Thread writer = new Thread(() -> {
      try (OutputStream output = process.getOutputStream()) {
        output.write(stdin.getBytes(StandardCharsets.UTF_8));
      } catch (IOException ignored) {}
    });
    writer.setDaemon(true);
    stdout.start(); stderr.start(); writer.start();
    StepResult result = new StepResult();
    result.timedOut = !process.waitFor(timeout, TimeUnit.SECONDS);
    if (result.timedOut) {
      process.descendants().forEach(child -> { try { child.destroyForcibly(); } catch (RuntimeException ignored) {} });
      process.destroyForcibly();
      process.waitFor(2, TimeUnit.SECONDS);
    }
    writer.join(1000); stdout.join(2000); stderr.join(2000);
    result.exitCode = process.isAlive() ? null : process.exitValue();
    result.stdout = stdout.text(); result.stderr = stderr.text();
    result.truncated = stdout.truncated || stderr.truncated;
    result.status = result.timedOut ? "runtime_timeout"
      : result.exitCode == null || result.exitCode != 0 ? "runtime_error" : "completed";
    if (result.timedOut && result.stderr.isEmpty())
      result.stderr = "Program exceeded " + timeout + " seconds. Check loop exit conditions or missing input.";
    for (Map.Entry<String, String> expected : expectedFiles.entrySet()) {
      String actual = null;
      if (safeName(expected.getKey())) {
        Path file = folder.resolve(expected.getKey());
        if (Files.isRegularFile(file, LinkOption.NOFOLLOW_LINKS) && Files.size(file) <= 64000) {
          try { actual = Files.readString(file, StandardCharsets.UTF_8); } catch (IOException ignored) {}
        }
      }
      result.fileChecks.add(new String[] { expected.getKey(), expected.getValue(), actual == null ? "\u0000" : actual });
    }
    return result;
  }
  private static void writeFiles(Path folder, Map<String, String> files) throws IOException {
    for (Map.Entry<String, String> item : files.entrySet()) {
      if (!safeName(item.getKey()) || item.getValue().getBytes(StandardCharsets.UTF_8).length > 64000)
        throw new IOException("Invalid or oversized data file fixture.");
      Path file = folder.resolve(item.getKey()).normalize();
      if (!file.getParent().equals(folder.normalize())) throw new IOException("Data file escaped its workspace.");
      Files.writeString(file, item.getValue(), StandardCharsets.UTF_8,
        StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING, StandardOpenOption.WRITE);
    }
  }
  private static String filesJson(Path folder) throws IOException {
    StringBuilder json = new StringBuilder("[");
    int count = 0;
    try (DirectoryStream<Path> paths = Files.newDirectoryStream(folder)) {
      for (Path file : paths) {
        if (count >= 50) break;
        String name = file.getFileName().toString();
        if (!safeName(name) || !Set.of(".txt", ".csv", ".json", ".md", ".log", ".dat")
            .contains(name.substring(name.lastIndexOf('.') < 0 ? name.length() : name.lastIndexOf('.')).toLowerCase(Locale.ROOT))
            || !Files.isRegularFile(file, LinkOption.NOFOLLOW_LINKS) || Files.size(file) > 64000) continue;
        String content;
        try { content = Files.readString(file, StandardCharsets.UTF_8); } catch (IOException ignored) { continue; }
        if (count++ > 0) json.append(',');
        json.append("{\"name\":").append(quote(name)).append(",\"content\":").append(quote(content)).append('}');
      }
    }
    return json.append(']').toString();
  }
  private static String stepJson(StepResult step) {
    StringBuilder json = new StringBuilder("{\"status\":").append(quote(step.status))
      .append(",\"stdout\":").append(quote(step.stdout)).append(",\"stderr\":").append(quote(step.stderr))
      .append(",\"exit_code\":").append(step.exitCode == null ? "null" : step.exitCode)
      .append(",\"timed_out\":").append(step.timedOut).append(",\"output_truncated\":").append(step.truncated)
      .append(",\"files\":[");
    for (int index = 0; index < step.fileChecks.size(); index++) {
      if (index > 0) json.append(',');
      String[] file = step.fileChecks.get(index);
      boolean matches = !"\u0000".equals(file[2]) && normalize(file[1]).equals(normalize(file[2]));
      json.append("{\"name\":").append(quote(file[0])).append(",\"expected\":").append(quote(file[1]))
        .append(",\"actual\":").append("\u0000".equals(file[2]) ? "null" : quote(file[2]))
        .append(",\"passed\":").append(matches).append('}');
    }
    return json.append("]}").toString();
  }
  private static String readString(BufferedReader reader) throws IOException { return decoded(reader); }
  public static void main(String[] args) {
    String report;
    try {
      BufferedReader reader = new BufferedReader(new StringReader(new String(Base64.getDecoder().decode(CONFIG), StandardCharsets.UTF_8)));
      String learnerSource = readString(reader);
      int caseCount = Integer.parseInt(line(reader));
      boolean collectFiles = "1".equals(line(reader));
      List<Map<String, Object>> cases = new ArrayList<>();
      List<Path> workspaces = new ArrayList<>();
      List<List<List<StepResult>>> results = new ArrayList<>();
      Path root = Files.createTempDirectory("fieldnotes-");
      Path compileDir = Files.createDirectory(root.resolve("classes"));
      Path sourceFile = root.resolve("Main.java");
      Files.writeString(sourceFile, learnerSource, StandardCharsets.UTF_8);
      ByteArrayOutputStream compilerOut = new ByteArrayOutputStream();
      ByteArrayOutputStream compilerErr = new ByteArrayOutputStream();
      var compiler = ToolProvider.getSystemJavaCompiler();
      int compileCode = compiler == null ? 2 : compiler.run(null, compilerOut, compilerErr,
        "--release", "21", "-encoding", "UTF-8", "-proc:none", "-d", compileDir.toString(), sourceFile.toString());
      String compileMessage = compilerErr.toString(StandardCharsets.UTF_8) + compilerOut.toString(StandardCharsets.UTF_8);
      if (compileCode != 0) {
        report = "{\"status\":\"compile_error\",\"compile_success\":false,\"compile_stderr\":" + quote(compileMessage)
          + ",\"cases\":[],\"files\":[]}";
      } else {
        for (int caseIndex = 0; caseIndex < caseCount; caseIndex++) {
          String caseName = decoded(reader);
          int fileCount = Integer.parseInt(line(reader));
          Map<String, String> initialFiles = new LinkedHashMap<>();
          for (int fileIndex = 0; fileIndex < fileCount; fileIndex++) initialFiles.put(decoded(reader), decoded(reader));
          int stepCount = Integer.parseInt(line(reader));
          Path folder = Files.createDirectory(root.resolve("case-" + caseIndex));
          workspaces.add(folder);
          writeFiles(folder, initialFiles);
          List<StepResult> caseResults = new ArrayList<>();
          boolean passed = true;
          StringBuilder caseJson = new StringBuilder("{\"name\":").append(quote(caseName)).append(",\"runs\":[");
          for (int stepIndex = 0; stepIndex < stepCount; stepIndex++) {
            String stdin = decoded(reader);
            int timeout = Integer.parseInt(line(reader));
            boolean hasExpected = "1".equals(line(reader));
            String expectedStdout = decoded(reader);
            int expectedFileCount = Integer.parseInt(line(reader));
            Map<String, String> expectedFiles = new LinkedHashMap<>();
            for (int fileIndex = 0; fileIndex < expectedFileCount; fileIndex++) expectedFiles.put(decoded(reader), decoded(reader));
            StepResult step = execute(compileDir, folder, stdin, Math.min(8, Math.max(1, timeout)), expectedFiles);
            caseResults.add(step);
            boolean stepPassed = step.status.equals("completed") && !step.truncated
              && (!hasExpected || normalize(step.stdout).equals(normalize(expectedStdout)));
            for (String[] file : step.fileChecks) {
              boolean filePassed = !"\u0000".equals(file[2]) && normalize(file[1]).equals(normalize(file[2]));
              stepPassed &= filePassed;
            }
            passed &= stepPassed;
            if (stepIndex > 0) caseJson.append(',');
            caseJson.append(stepJson(step));
            if (!step.status.equals("completed")) {
              for (int skipped = stepIndex + 1; skipped < stepCount; skipped++) {
                decoded(reader); line(reader); line(reader); decoded(reader);
                int files = Integer.parseInt(line(reader));
                for (int fileIndex = 0; fileIndex < files; fileIndex++) { decoded(reader); decoded(reader); }
                StepResult missing = new StepResult(); missing.status = "skipped"; missing.stdout = "";
                missing.stderr = "Earlier run failed; this restart step was not executed."; missing.fileChecks = new ArrayList<>();
                caseResults.add(missing); caseJson.append(',').append(stepJson(missing));
              }
              break;
            }
          }
          caseJson.append("],\"passed\":").append(passed).append('}');
          @SuppressWarnings("unchecked") Map<String, Object> item = new HashMap<>();
          item.put("json", caseJson.toString()); item.put("passed", passed);
          cases.add(item);
          results.add(new ArrayList<>(List.of(caseResults)));
        }
        StringBuilder caseJson = new StringBuilder("[");
        boolean allPassed = caseCount > 0;
        for (int index = 0; index < cases.size(); index++) {
          if (index > 0) caseJson.append(',');
          caseJson.append(cases.get(index).get("json"));
          allPassed &= (Boolean)cases.get(index).get("passed");
        }
        String files = collectFiles && !workspaces.isEmpty() ? filesJson(workspaces.get(0)) : "[]";
        report = "{\"status\":\"compiled\",\"compile_success\":true,\"compile_stderr\":" + quote(compileMessage)
          + ",\"passed\":" + allPassed + ",\"cases\":" + caseJson.append(']') + ",\"files\":" + files + "}";
      }
      removeTree(root);
    } catch (Throwable error) {
      report = "{\"status\":\"runner_error\",\"compile_success\":false,\"compile_stderr\":" + quote(error.toString())
        + ",\"cases\":[],\"files\":[]}";
    }
    System.out.println("__FIELDNOTES_RESULT__" + report);
  }
}
`

export function makeHarness(config: HarnessConfig): string {
  return JAVA_HARNESS.replace('__CONFIG__', protocol(config))
}
