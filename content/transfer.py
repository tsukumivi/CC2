"""Novel-domain programs for revisiting each stage, not extra core gates."""
from content.authoring import J, P, T

SCANNER = 'import java.util.Scanner;'
IO = 'import java.nio.file.*;\nimport java.nio.charset.StandardCharsets;\nimport java.io.IOException;'

POSTCARD = J('System.out.println("Mars report");\nSystem.out.println("Ready");\nSystem.out.println("End of transmission");')
DURATION = J('int minutes = 125;\nint hours = minutes / 60;\nint remaining = minutes % 60;\nSystem.out.println("Hours: " + hours);\nSystem.out.println("Minutes: " + remaining);')
STATION = J('Scanner in = new Scanner(System.in);\nString city = in.nextLine().trim().toUpperCase(java.util.Locale.ROOT);\nSystem.out.println("Station: " + city);', SCANNER)
PARCEL = J('''Scanner in = new Scanner(System.in);
if (!in.hasNextLine()) return;
try {
    int weight = Integer.parseInt(in.nextLine().trim());
    if (weight < 1 || weight > 50) System.out.println("Invalid");
    else if (weight <= 10) System.out.println("Small");
    else System.out.println("Large");
} catch (NumberFormatException error) { System.out.println("Invalid"); }''', SCANNER)
SCORES = J('''Scanner in = new Scanner(System.in);
int count = 0;
int total = 0;
while (in.hasNextLine()) {
    String line = in.nextLine().trim();
    if (line.equals("q")) break;
    try {
        int score = Integer.parseInt(line);
        if (score < 0 || score > 10) { System.out.println("Invalid"); continue; }
        count++;
        total += score;
    } catch (NumberFormatException error) { System.out.println("Invalid"); }
}
System.out.println("Count: " + count);
System.out.println("Total: " + total);''', SCANNER)
TEMPERATURE = J('''Scanner in = new Scanner(System.in);
if (!in.hasNextLine()) return;
try {
    double c = Double.parseDouble(in.nextLine().trim());
    double f = fahrenheit(c);
    if (!Double.isFinite(c) || c < -273.15 || !Double.isFinite(f)) System.out.println("Invalid");
    else System.out.println(f);
} catch (NumberFormatException error) { System.out.println("Invalid"); }''', SCANNER,
    'static double fahrenheit(double c) { return c * 9 / 5.0 + 32; }')
BOOKS = J(r'''Scanner in = new Scanner(System.in);
java.util.ArrayList<Book> books = new java.util.ArrayList<>();
while (in.hasNextLine()) {
    String line = in.nextLine();
    if (line.trim().equals("q")) break;
    String[] parts = line.split("\\|", -1);
    if (parts.length != 2 || parts[0].trim().isEmpty()) { System.out.println("Invalid"); continue; }
    try {
        int pages = Integer.parseInt(parts[1].trim());
        if (pages < 0 || pages > 10000) { System.out.println("Invalid"); continue; }
        books.add(new Book(parts[0].trim(), pages));
        System.out.println("Queued");
    } catch (NumberFormatException error) { System.out.println("Invalid"); }
}
int total = 0;
for (Book book : books) total += book.getPages();
System.out.println("Pages: " + total);''', SCANNER, '''static class Book {
    private final String title;
    private final int pages;
    Book(String title, int pages) {
        if (title.isEmpty() || pages < 0 || pages > 10000) throw new IllegalArgumentException("book");
        this.title = title;
        this.pages = pages;
    }
    String getTitle() { return title; }
    int getPages() { return pages; }
}''')
VISITS = J('''Path file = Path.of("visits.txt");
int visits = 0;
try {
    if (!Files.notExists(file)) visits = Integer.parseInt(Files.readString(file, StandardCharsets.UTF_8).trim());
    if (visits < 0 || visits > 1000000) throw new IllegalArgumentException("visits");
} catch (IOException | IllegalArgumentException error) { System.out.println("Load failed"); return; }
if (visits == 1000000) { System.out.println("Full"); return; }
try {
    save(file, visits + 1);
    System.out.println("Visits: " + (visits + 1));
} catch (IOException error) { System.out.println("Save failed"); }''', IO, '''static void save(Path file, int visits) throws IOException {
    Path temporary = Files.createTempFile(file.toAbsolutePath().getParent(), "visits-", ".tmp");
    try {
        Files.writeString(temporary, visits + "\\n", StandardCharsets.UTF_8);
        try {
            Files.move(temporary, file, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
        } catch (AtomicMoveNotSupportedException error) {
            Files.move(temporary, file, StandardCopyOption.REPLACE_EXISTING);
        }
    } finally { Files.deleteIfExists(temporary); }
}''')

TRANSFER = {
    'first-success': P('Transfer / mission postcard. Without input, print exactly three lines: Mars report, Ready, End of transmission. Use a complete Main class and three output statements; no solution is supplied in the editor.', POSTCARD,
        [T('postcard lines', '', 'Mars report\nReady\nEnd of transmission\n'), T('no input required', 'ignored\n', 'Mars report\nReady\nEnd of transmission\n')]),
    'values': P('Transfer / a time display. Store 125 minutes in a named int variable. Calculate whole hours and remaining minutes using division and remainder. Print Hours: 2 then Minutes: 5 on separate lines. Do not hardcode the calculated answers.', DURATION,
        [T('duration calculation', '', 'Hours: 2\nMinutes: 5\n'), T('input not used', 'ignored\n', 'Hours: 2\nMinutes: 5\n')], rubric=['I derive hours and remaining minutes from the stored value.', 'I can explain why integer division is intentional here.']),
    'input-text': P('Transfer / weather station label. Read one supplied full city line, trim its surrounding whitespace and uppercase it with Locale.ROOT so the result is independent of the computer locale. Print Station: followed by one space and the result. Empty text is allowed; input is guaranteed to contain one line.', STATION,
        [T('whole city name', ' New Oslo \n', 'Station: NEW OSLO\n'), T('empty label', '\n', 'Station: \n'), T('UTF-8 city', '星の町\n', 'Station: 星の町\n')], starter=J('// Read a whole line. Normalize text before creating its label.', SCANNER)),
    'decisions': P('Transfer / parcel classifier. Read one line containing an integer weight. Trim it. Values 1..10 print Small; 11..50 print Large. Out-of-range or non-integer text prints Invalid. If no line is supplied, print nothing. No loop is needed.', PARCEL,
        [T('small boundary', '10\n', 'Small\n'), T('large boundary', '11\n', 'Large\n'), T('upper limit', '50\n', 'Large\n'), T('reject zero', '0\n', 'Invalid\n'), T('reject decimal', '1.5\n', 'Invalid\n'), T('empty EOF', '', '')], starter=J('// Validate the line before selecting its size category.', SCANNER)),
    'repetition': P('Transfer / quiz score tally. Read whole lines until trimmed q or EOF. Accept integers 0..10; count and total only accepted values. Print Invalid for each rejected line and continue. At exit print Count: followed by count, then Total: followed by total, each after one space. Do not print a prompt.', SCORES,
        [T('two scores', '2\n8\nq\n', 'Count: 2\nTotal: 10\n'), T('recover and count zero', 'bad\n11\n0\nq\n', 'Invalid\nInvalid\nCount: 1\nTotal: 0\n'), T('EOF tally', '10\n', 'Count: 1\nTotal: 10\n'), T('empty tally', '', 'Count: 0\nTotal: 0\n')], starter=J('// Retry bad scores without adding them to the count or total.', SCANNER)),
    'structure': P('Transfer / temperature tool. Write a fahrenheit(double c) method returning c * 9 / 5.0 + 32. Read one trimmed whole line; parse it as a double. Reject non-numeric, non-finite, below -273.15, or non-finite converted values with Invalid. Otherwise print the converted double. EOF without a line prints nothing.', TEMPERATURE,
        [T('freezing', '0\n', '32.0\n'), T('shared scale value', '-40\n', '-40.0\n'), T('decimal arithmetic', '100\n', '212.0\n'), T('reject NaN', 'NaN\n', 'Invalid\n'), T('below absolute zero', '-274\n', 'Invalid\n'), T('overflow check', '1e308\n', 'Invalid\n')], starter=J('// Separate conversion from input parsing and validation.', SCANNER), rubric=['I put the conversion in a parameterized method that returns a value.', 'I validate both the input and calculated result; I catch the specific parse failure.']),
    'records': P('Transfer / reading queue. Read title|pages lines until trimmed q or EOF. Trim both fields; title must be nonempty and pages an integer 0..10000. Reject bad shapes or values with Invalid and continue. Queue valid Book objects in an ArrayList and print Queued for each. Duplicate titles are allowed as distinct editions. At exit traverse the objects and print Pages: plus one space and their total. Use private fields, a validating constructor and a page getter.', BOOKS,
        [T('two editions', 'Orbit|120\nOrbit|80\nq\n', 'Queued\nQueued\nPages: 200\n'), T('recover and upper boundary', '|2\nMoon|bad\n星|10000\nq\n', 'Invalid\nInvalid\nQueued\nPages: 10000\n'), T('zero and bad shape', 'Zero|0\nA|B|3\nq\n', 'Queued\nInvalid\nPages: 0\n'), T('empty EOF', '', 'Pages: 0\n')], starter=J('// Define Book and build a reading queue, not the inventory manager.', SCANNER), rubric=['I keep title and page count together in objects with private fields.', 'I validate construction and derive the total by traversing stored objects.']),
    'persistence': P('Transfer / persistent visitor counter. Before accepting any input, load UTF-8 visits.txt, whose trimmed content is one integer 0..1000000. Missing file starts at zero. Any other load problem prints Load failed and leaves the file unchanged. At one million print Full and leave it unchanged. Otherwise increment once, stage a sibling temporary file and replace visits.txt, then print Visits: plus one space and the new count. Write a newline after the stored number. On I/O write failure print Save failed, never Visits. Demonstrate two separate runs in the same saved-project workspace.', VISITS,
        [{'name':'counter restart', 'runs':[T('first process', '', 'Visits: 1\n', expected_files={'visits.txt':'1\n'}), T('second process', '', 'Visits: 2\n', expected_files={'visits.txt':'2\n'})]}, T('protect corrupt count', '', 'Load failed\n', files={'visits.txt':'bad\n'}, expected_files={'visits.txt':'bad\n'}), T('upper boundary', '', 'Full\n', files={'visits.txt':'1000000\n'}, expected_files={'visits.txt':'1000000\n'}), T('last increment', '', 'Visits: 1000000\n', files={'visits.txt':'999999\n'}, expected_files={'visits.txt':'1000000\n'})], starter=J('// Load safely, increment within the range, stage the write and report its actual outcome.', IO), rubric=['My restart test uses separate processes in one persistent directory.', 'I preserve corrupt or full files and stage the successful replacement.']),
}

for module, task in TRANSFER.items():
    task.update(required=False, transfer=True, id=module+'-transfer-build')
