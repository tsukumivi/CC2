from content.authoring import E, J, L, P, Q, R, T
from content.units.input_text import SCANNER
from content.units.records import INVENTORY_MEMBERS

IO_IMPORTS = 'import java.util.Scanner;\nimport java.nio.file.*;\nimport java.nio.charset.StandardCharsets;\nimport java.io.IOException;'
WRITE = J('Scanner in = new Scanner(System.in);\nString note = in.nextLine();\ntry {\n    Files.writeString(Path.of("note.txt"), note + "\\n", StandardCharsets.UTF_8);\n    System.out.println("Saved");\n} catch (IOException error) { System.out.println("Save failed"); }', IO_IMPORTS)
READ = J('try {\n    String text = Files.readString(Path.of("note.txt"), StandardCharsets.UTF_8);\n    System.out.print(text);\n} catch (NoSuchFileException error) {\n    System.out.println("No saved note");\n} catch (IOException error) {\n    System.out.println("Read failed");\n}', IO_IMPORTS)
APPEND = J('Scanner in = new Scanner(System.in);\nString line = in.nextLine();\ntry (java.io.BufferedWriter writer = Files.newBufferedWriter(Path.of("log.txt"), StandardCharsets.UTF_8, StandardOpenOption.CREATE, StandardOpenOption.APPEND)) {\n    writer.write(line);\n    writer.newLine();\n} catch (IOException error) { System.out.println("Save failed"); return; }\nSystem.out.println("Appended");', IO_IMPORTS)
PERSIST_MEMBERS = INVENTORY_MEMBERS + r'''
static java.util.ArrayList<Item> load(Path file) throws IOException {
    java.util.ArrayList<Item> items = new java.util.ArrayList<>();
    if (Files.notExists(file)) return items;
    for (String line : Files.readAllLines(file, StandardCharsets.UTF_8)) {
        String[] parts = line.split("\\|", -1);
        if (parts.length != 2 || !validTitle(parts[0]) || !parts[0].equals(parts[0].trim())) {
            throw new IllegalArgumentException("format");
        }
        int quantity = Integer.parseInt(parts[1]);
        if (quantity < 0 || quantity > 1000 || find(items, parts[0]) != null) {
            throw new IllegalArgumentException("record");
        }
        items.add(new Item(parts[0], quantity));
    }
    return items;
}
static void save(Path file, java.util.ArrayList<Item> items) throws IOException {
    StringBuilder text = new StringBuilder();
    for (Item item : items) text.append(item.getTitle()).append('|').append(item.getQuantity()).append('\n');
    Path temporary = Files.createTempFile(file.toAbsolutePath().getParent(), "records-", ".tmp");
    try {
        Files.writeString(temporary, text, StandardCharsets.UTF_8);
        try {
            Files.move(temporary, file, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
        } catch (AtomicMoveNotSupportedException error) {
            Files.move(temporary, file, StandardCopyOption.REPLACE_EXISTING);
        }
    } finally {
        Files.deleteIfExists(temporary);
    }
}
static boolean remove(java.util.ArrayList<Item> items, String title) {
    for (int i = 0; i < items.size(); i++) {
        if (items.get(i).getTitle().equals(title)) { items.remove(i); return true; }
    }
    return false;
}'''.replace("append('\\\\n')", "append('\\n')")
PERSIST_BODY = r'''Scanner in = new Scanner(System.in);
Path file = Path.of("records.txt");
java.util.ArrayList<Item> items;
try { items = load(file); }
catch (IOException | IllegalArgumentException error) { System.out.println("Load failed"); return; }
while (in.hasNextLine()) {
    String line = in.nextLine().trim();
    if (line.equals("q")) { System.out.println("Bye"); break; }
    if (line.equals("list")) { list(items); continue; }
    if (line.equals("save")) {
        try { save(file, items); System.out.println("Saved"); }
        catch (IOException error) { System.out.println("Save failed"); }
        continue;
    }
    String[] parts = line.split("\\|", -1);
    if (parts.length == 3 && parts[0].equals("add")) {
        String title = parts[1].trim();
        try {
            int quantity = Integer.parseInt(parts[2].trim());
            if (!validTitle(title) || quantity < 0 || quantity > 1000) { System.out.println("Invalid"); continue; }
            if (find(items, title) != null) { System.out.println("Duplicate"); continue; }
            items.add(new Item(title, quantity));
            System.out.println("Added");
        } catch (NumberFormatException error) { System.out.println("Invalid"); }
    } else { System.out.println("Unknown"); }
}'''
PERSIST = J(PERSIST_BODY, IO_IMPORTS, PERSIST_MEMBERS)
CAPSTONE_BODY = PERSIST_BODY.replace('    } else { System.out.println("Unknown"); }', '''    } else if (parts.length == 2 && parts[0].equals("remove")) {
        String title = parts[1].trim();
        if (!validTitle(title)) System.out.println("Invalid");
        else System.out.println(remove(items, title) ? "Removed" : "Not found");
    } else { System.out.println("Unknown"); }''')
CAPSTONE = J(CAPSTONE_BODY, IO_IMPORTS, PERSIST_MEMBERS)
RESTART = {'name': 'save then restart', 'runs': [T('first process', 'add|Orbit|2\nsave\nq\n', 'Added\nSaved\nBye\n', expected_files={'records.txt': 'Orbit|2\n'}), T('second process', 'list\nq\n', 'Orbit|2\nBye\n')]}

LESSONS = [
L('file-write', 'Save UTF-8 Text', 'Distinguish local memory from a real file and define overwrite behavior.',
  ['Path.of("note.txt") identifies a file relative to the program’s working directory. Files.writeString with UTF-8 creates the file if needed and, with default options, replaces existing content. It does not append unless you request append options.',
   'Use an explicit encoding so non-English text survives a round trip. IOException represents a file operation failure; report it truthfully rather than printing Saved after a failed write.',
   'Task validation creates fresh workspaces, so it cannot overwrite your project files. In the Code Bench, save/open a project first to get its persistent workspace. Unsaved scratch runs use temporary folders whose files are discarded after the run.'],
  ['Write a real UTF-8 file with explicit replace semantics.', 'Report a failed file operation without claiming success.'],
  E(WRITE, 'Saved\n', ['Read one note line.', 'Create or replace note.txt in the working directory.', 'Write UTF-8 plus a newline.', 'Print Saved only after a successful write.'], 'Orbit\n', expected_files={'note.txt': 'Orbit\n'}),
  Q('The file contains Old. A successful default writeString writes New. What text remains: OldNew or New?', '', 'New', 'Default writeString replaces old content; it is not an append operation.'),
  R('Where is note.txt written, and why is an unsaved scratch run not a persistence demonstration?', 'The file is relative to the program’s working directory. Scratch workspaces are deleted after a run; use the same saved-project workspace or an external folder across runs.', ['I distinguish relative paths from the source file location.', 'I state overwrite semantics and UTF-8.', 'I use a persistent workspace for a restart test.']),
  P('Read one supplied line, write it plus a newline to note.txt in UTF-8, replacing any old file, and print Saved. On IOException print Save failed.', WRITE, [T('UTF-8 save', '星の旅\n', 'Saved\n', expected_files={'note.txt':'星の旅\n'}), T('replace old content', 'New\n', 'Saved\n', files={'note.txt':'Old\n'}, expected_files={'note.txt':'New\n'})], starter=J('Scanner in = new Scanner(System.in);\n// Read, write note.txt in UTF-8, and report the actual result.', IO_IMPORTS))),
L('file-read', 'Load, or Explain Why You Cannot', 'Treat a missing file differently from a corrupt or unreadable file.',
  ['Files.readString reads the file using the specified encoding. A missing file raises NoSuchFileException, a specific IOException subtype. Catch it before IOException if you want a distinct first-run message.',
   'A file that exists but cannot be read is not the same as an absent file. Do not replace every read failure with an empty dataset and automatically save it: that can destroy previously saved data. The record manager will fail closed on bad data.',
   'Read only the documented format you know how to interpret. This simple note program prints stored text unchanged, so print is used instead of adding an extra newline with println.'],
  ['Read UTF-8 text without adding unintended characters.', 'Distinguish a missing first-run file from another read failure.'],
  E(READ, 'Orbit\n', ['Read note.txt.', 'Print the stored text exactly.', 'A missing file takes the specific catch.'], files={'note.txt':'Orbit\n'}),
  Q('No note.txt exists. What exact line does the example print?', READ, 'No saved note', 'The specific missing-file handler runs.'),
  R('Why should a record manager stop rather than silently use an empty list when an existing file is malformed?', 'An empty replacement can later overwrite the original data. Stop with a load error and preserve the file so the user can inspect or repair it.', ['I distinguish absence from malformed existing data.', 'I avoid overwriting data after a failed load.']),
  P('Read note.txt in UTF-8 and print its exact contents. If it is missing print No saved note. On another IOException print Read failed. Do not write any file.', READ, [T('stored UTF-8', '', '星の旅\n', files={'note.txt':'星の旅\n'}, expected_files={'note.txt':'星の旅\n'}), T('missing first-run note', '', 'No saved note\n'), T('empty stored note', '', '', files={'note.txt':''})], starter=J('// Read note.txt. Catch a missing file separately; do not write a replacement.', IO_IMPORTS))),
L('file-resources', 'Append & Close a File Handle', 'Use try-with-resources and explicit append options.',
  ['Some file APIs give you an open reader or writer. try (resource declaration) closes an AutoCloseable resource when the block exits, even on failure. Closing the writer flushes buffered data and releases the handle.',
   'CREATE and APPEND create the log if absent and add at its end if present. These differ from the default replace behavior. writer.newLine writes the platform newline; a portable reader should accept the platform’s line endings.',
   'Keep success output after the try-with-resources block. A failure while writing or closing must not be reported as a successful append. This program accepts one line per run; multiple runs share the file only in a persistent workspace.'],
  ['Close a writer reliably with try-with-resources.', 'Choose append versus replace from the requirement.'],
  E(APPEND, 'Appended\n', ['Open or create log.txt in append mode.', 'Write the supplied line and a newline.', 'Automatically close the writer.', 'Report success afterward.'], 'Second\n', files={'log.txt':'First\n'}, expected_files={'log.txt':'First\nSecond\n'}),
  Q('log.txt starts with First on one line. Append Second with a newline. Write the two stored lines.', '', 'First\nSecond', 'Append preserves the first line and adds the second.'),
  R('Why is try-with-resources preferable to remembering a close call only on the success path?', 'It closes the resource on both normal and exceptional exit. A success-only close can leave handles and buffers open after a failure.', ['I mention exceptional cleanup.', 'I distinguish append from replacing old content.']),
  P('Read one supplied line, append it and a newline to UTF-8 log.txt using try-with-resources, and print Appended. On IOException print Save failed.', APPEND, [T('create log', 'Start\n', 'Appended\n', expected_files={'log.txt':'Start\n'}), T('preserve earlier line', 'Next\n', 'Appended\n', files={'log.txt':'Start\n'}, expected_files={'log.txt':'Start\nNext\n'})], starter=J('Scanner in = new Scanner(System.in);\n// Read a line and append with an automatically closed BufferedWriter.', IO_IMPORTS), rubric=['I use try-with-resources for the writer.', 'I append without truncating the earlier lines.'])),
L('persistent-inventory', 'Milestone: Records That Survive Restart', 'Save a documented format and prove that a new process can load it.',
  ['Build on the in-memory manager with save. records.txt is UTF-8 with one title|quantity record per line, no header, insertion order, case-sensitive unique titles, and quantities 0..1000. Missing file means an empty first run. An empty file is a valid empty inventory.',
   'An existing malformed file is different from a missing file. Load validates every row and rejects duplicate titles, bad quantities, empty fields and bad shapes. On any load problem print Load failed and stop without saving. Keep the original file for inspection.',
   'save serializes the current list with StringBuilder, writes a temporary sibling file, then replaces records.txt. Try an atomic move where supported, with a replace-move fallback. Finally remove the temporary file if it remains. This staging reduces the risk of truncating a good file during a failed write; it is not a full transactional database.',
   'q does not autosave. An explicit save prints Saved or Save failed. Restart testing means two separate Java processes with the same working directory: add/save/quit in the first, list/quit in the second. Reading from the same in-memory object is not a restart test.'],
  ['Specify and validate a simple record file format.', 'Demonstrate persistence across separate processes.'],
  E(PERSIST, 'Added\nSaved\nBye\n', ['A missing file loads an empty list.', 'Add one validated record.', 'Save to records.txt.', 'The next process can reconstruct the record.'], 'add|Orbit|2\nsave\nq\n', expected_files={'records.txt':'Orbit|2\n'}),
  Q('records.txt contains Orbit|2 followed by a newline. Input is list then q. Write the exact output lines.', PERSIST, 'Orbit|2\nBye', 'The new process loads the file before dispatching list.'),
  R('Describe a real restart test and what the manager should do if its existing file is malformed.', 'Run add/save/q, start a new process in the same directory, then list/q. If loading malformed data fails, report Load failed and preserve that file without accepting commands or saving.', ['I use two processes sharing one directory.', 'I distinguish missing from malformed data.', 'I preserve the original file on load failure.']),
  P('Implement the documented persistent inventory with add|title|quantity, list, save and q. Use validated Item objects, separate load/save/find/list methods, UTF-8 records.txt and truthful load/save failure messages. Do not autosave on q.', PERSIST, [RESTART, T('corrupt file preserved', 'save\nq\n', 'Load failed\n', files={'records.txt':'Orbit|bad\n'}, expected_files={'records.txt':'Orbit|bad\n'}), T('first-run empty', 'list\nsave\nq\n', 'Empty\nSaved\nBye\n', expected_files={'records.txt':''})], starter=J('// Define Item and small methods. Load first, dispatch commands, and save only on request.', IO_IMPORTS), hints=['Write load/save as separate operations with one documented format.', 'Do not treat a corrupt existing file as an empty first run.'], rubric=['I validate every loaded record before accepting commands.', 'I use the same project workspace for the restart demonstration.', 'My save failure does not claim Saved.'])),
L('external-run', 'Run Without the Studio', 'Export Main.java and reproduce a saved-data run from a terminal.',
  ['Download your project as Main.java and put it in an ordinary working folder. With a full JDK 21 or newer, run javac --release 21 -encoding UTF-8 Main.java, then java -Dfile.encoding=UTF-8 Main. The public class name must match the filename.',
   'The terminal supplies live standard input. Type commands one per line and use q to exit. Relative files such as records.txt belong to the current working directory, not a magic Studio location. Keep the same folder for a restart.',
   'To move a saved project, export its data file from the Studio as well as Main.java. Copy records.txt alongside the source in your working folder. A code-only export does not include database progress or persistent data.'],
  ['Compile and run an exported program with a full JDK.', 'Identify and carry the data files needed for a portable restart.'],
  E(J('System.out.println("Portable Java");'), 'Portable Java\n', ['Save Main.java.', 'Compile with javac.', 'Run the compiled Main class.']),
  Q('Which command runs the compiled Main class: java Main or javac Main.java?', '', 'java Main', 'javac compiles; java starts the compiled class.'),
  R('Give the compile/run commands and explain where records.txt must be for a portable project.', 'Compile with javac --release 21 -encoding UTF-8 Main.java. Run java -Dfile.encoding=UTF-8 Main from the folder containing the desired records.txt. Export code and data separately.', ['I use javac before java.', 'I keep Main.java and its public class name consistent.', 'I carry the data file and use the correct working directory.']),
  P('Create an exportable Main that reads one supplied full line and prints Portable: followed by one space and that line. Then download it and follow the external compile/run instructions.', J('Scanner in = new Scanner(System.in);\nSystem.out.println("Portable: " + in.nextLine());', SCANNER), [T('external input contract', 'Orbit\n', 'Portable: Orbit\n'), T('UTF-8 portability', '星の旅\n', 'Portable: 星の旅\n')], rubric=['My exported filename is Main.java.', 'I have recorded the external commands; Studio checks alone do not prove my manual external trial.'])),
L('capstone-records', 'Capstone: an Independent Record Manager', 'Build, test, save and explain a program without copying the reference.',
  ['Implement a small stock/watchlist manager from this specification: add|title|quantity, remove|title, list, save, q. Keep the previous title/range/uniqueness rules. remove prints Removed or Not found; an invalid title prints Invalid. Other command shapes print Unknown.',
   'Use Item objects in ArrayList<Item>. Separate input dispatch, validation, find/remove/list, load and save into methods. For indexed removal, stop immediately after removing the matching item so shifted positions are not accidentally skipped.',
   'Load records.txt before accepting commands, using the documented UTF-8 title|quantity format. Missing file is a fresh empty inventory; malformed existing data prints Load failed and stops without changing the file. Save only on save, with Saved or Save failed.',
   'Make a test table before coding. Include empty list, zero quantity, maximum quantity, bad numeric text, duplicate title, missing removal target, malformed command, EOF and a two-process restart. Explain one repair in terms of its failing test.',
   'Passing supplied checks is not professional certification. Add a new record domain and a new requirement without the solution open, export code and data, and run it outside the Studio. A human learner trial is still needed to measure whether this course supports independent transfer.'],
  ['Deliver a maintainable, recoverable record manager.', 'Prove saved data survives restart and explain the test evidence.'],
  E('', '', ['Start with an absent file: the inventory is empty.', 'An add operation validates before mutating.', 'A successful removal changes the stored collection.', 'Save is explicit; a new process loads the saved state.'], text='Requirement trace (not a complete solution):\nadd|Orbit|2 -> Added\nremove|Orbit -> Removed\nlist -> Empty\nsave -> Saved; records.txt is empty\nq -> Bye'),
  Q('An existing file contains Orbit|2. Input is remove|Moon then list then q. Write all output lines.', CAPSTONE, 'Not found\nOrbit|2\nBye', 'Removing an absent title must not erase the existing record.'),
  R('Explain your capstone’s data contract, recovery behavior, method boundaries and restart evidence. Include a new test you chose yourself.', 'Describe title and quantity rules, each command, specific conversion/I/O handling, small responsibility-based methods, a two-process save/load test and an independently chosen regression case.', ['I explain the format, uniqueness and ranges.', 'I show recovery and protection against corrupt loads.', 'I name my methods and why they are separate.', 'I describe two-process restart evidence and one additional test.']),
  P('Build the full specified manager from this requirement, without copying the reference. Commands and outputs are exact as described. Record a test table, demonstrate two-process persistence, and explain your design. Reference-assisted passes are practice, not independent completion.', CAPSTONE, [RESTART, T('recover and remove', 'add|Orbit|2\nadd|Orbit|5\nadd|Moon|bad\nremove|Moon\nremove|Orbit\nlist\nsave\nq\n', 'Added\nDuplicate\nInvalid\nNot found\nRemoved\nEmpty\nSaved\nBye\n', expected_files={'records.txt':''}), T('quantity boundaries and unknown', 'add|Zero|0\nadd|Max|1000\nadd|TooMuch|1001\nadd|A|B|3\nlist\nq\n', 'Added\nAdded\nInvalid\nUnknown\nZero|0\nMax|1000\nBye\n'), T('protect corrupt file', 'save\nq\n', 'Load failed\n', files={'records.txt':'Orbit|2\nOrbit|3\n'}, expected_files={'records.txt':'Orbit|2\nOrbit|3\n'}), T('empty EOF', '', '')], starter=J('// Start from the specification and your test table. Define records and small methods, then the command loop.', IO_IMPORTS), hints=['Implement and test memory-only commands first; add persistence after they work.', 'Use a separate load method that rejects corrupt existing data before any save.'], rubric=['I use record objects and responsibility-based methods.', 'I can explain the invalid-input and file-failure paths.', 'I have tested a separate restart and chosen an additional regression case.', 'I can adapt this program to a new domain without the solution open.']),
  diagram={'kind':'sequence','nodes':['Load & validate saved records','Read one command','Validate / mutate / list','Explicit save stages file replacement','Quit or EOF; new process loads file'],'edges':[[0,1],[1,2],[2,1],[2,3],[3,1],[1,4]]}),
]
