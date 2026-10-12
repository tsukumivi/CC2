from content.authoring import E, J, L, P, Q, R, T
from content.units.input_text import SCANNER

SEARCH = J('Scanner in = new Scanner(System.in);\nint n = in.nextInt();\nint[] values = new int[n];\nfor (int i = 0; i < n; i++) values[i] = in.nextInt();\nint target = in.nextInt();\nint found = -1;\nfor (int i = 0; i < values.length; i++) {\n    if (values[i] == target) { found = i; break; }\n}\nSystem.out.println(found);', SCANNER)
TITLES = J('Scanner in = new Scanner(System.in);\nint n = in.nextInt();\nin.nextLine();\njava.util.ArrayList<String> titles = new java.util.ArrayList<>();\nfor (int i = 0; i < n; i++) titles.add(in.nextLine());\nSystem.out.println("Count: " + titles.size());\nfor (String title : titles) System.out.println(title);', SCANNER)
ITEM_MEMBERS = 'static class Item {\n    String title;\n    int quantity;\n    Item(String title, int quantity) {\n        this.title = title;\n        this.quantity = quantity;\n    }\n}'
PRIVATE_ITEM = 'static class Item {\n    private final String title;\n    private int quantity;\n    Item(String title, int quantity) {\n        this.title = title;\n        setQuantity(quantity);\n    }\n    int getQuantity() { return quantity; }\n    String getTitle() { return title; }\n    void setQuantity(int quantity) {\n        if (quantity < 0 || quantity > 1000) throw new IllegalArgumentException("quantity");\n        this.quantity = quantity;\n    }\n}'
INVENTORY_MEMBERS = '''static class Item {
    private final String title;
    private final int quantity;
    Item(String title, int quantity) { this.title = title; this.quantity = quantity; }
    String getTitle() { return title; }
    int getQuantity() { return quantity; }
}
static boolean validTitle(String title) {
    return !title.isEmpty() && title.length() <= 20 && !title.contains("|");
}
static Item find(java.util.ArrayList<Item> items, String title) {
    for (Item item : items) if (item.getTitle().equals(title)) return item;
    return null;
}
static void list(java.util.ArrayList<Item> items) {
    if (items.isEmpty()) System.out.println("Empty");
    for (Item item : items) System.out.println(item.getTitle() + "|" + item.getQuantity());
}'''
INVENTORY_BODY = r'''Scanner in = new Scanner(System.in);
java.util.ArrayList<Item> items = new java.util.ArrayList<>();
while (in.hasNextLine()) {
    String line = in.nextLine().trim();
    if (line.equals("q")) { System.out.println("Bye"); break; }
    if (line.equals("list")) { list(items); continue; }
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
INVENTORY = J(INVENTORY_BODY, SCANNER, INVENTORY_MEMBERS)

LESSONS = [
L('arrays-and-search', 'Arrays & a First-Match Search', 'Store a fixed group and search without crossing its bounds.',
  ['An array has a fixed length and zero-based positions. new int[n] allocates n int slots initialized to zero. Access only indices from 0 through length - 1. The length field has no parentheses.',
   'A linear search checks each position until it finds a match. Use -1 to represent no match when valid positions begin at zero. Stop at the first matching position when the contract asks for the first match; duplicates make that rule important.',
   'An empty array is valid and has length zero. Its traversal loop must execute zero times. Do not read values[0] as an initial assumption when n can be zero. The input contract for this exercise supplies n and all required valid tokens.'],
  ['Allocate and traverse a fixed-size array safely.', 'Return a first matching index or a no-match sentinel.'],
  E(SEARCH, '1\n', ['Store three values at positions 0, 1 and 2.', 'Check positions in order.', 'The first target match is position 1.'], '3 4 8 8 8\n'),
  Q('For input 3 7 7 9 7, what index is printed?', SEARCH, '0', 'Both first positions contain 7, but the first-match search stops at index 0.'),
  R('What loop boundary and no-match result make this search safe for an empty array?', 'Use i < values.length so the empty array has no iterations. Keep found = -1 unless a match is found.', ['I use zero-based indices below length.', 'I preserve -1 when there is no match.', 'I do not access element zero for an empty array.']),
  P('Read n from 0..20, then n valid int values, then one target int. Print the zero-based first matching position or -1. Handle n = 0 and duplicate values.', SEARCH, [T('duplicates first match', '4 2 7 7 3 7\n', '1\n'), T('absent target', '2 4 5 9\n', '-1\n'), T('empty array', '0 9\n', '-1\n')], starter=J('Scanner in = new Scanner(System.in);\n// Read n, allocate and fill an array, read target, then search safely.', SCANNER))),
L('arraylist-collections', 'A Resizable List of Titles', 'Add, traverse and distinguish size from capacity.',
  ['ArrayList<String> stores a resizable sequence of String references. The type argument says what the list accepts. Use add to append, get(index) to read a position, size() for the element count and isEmpty() for the empty case.',
   'Unlike an array, a list can grow as records arrive. Its size is the current number of elements, not an exposed backing-array capacity. Valid indices still run from 0 to size() - 1.',
   'An enhanced for loop, for (String title : titles), visits each current element in order when you do not need its index. Avoid structural removal while using that loop. For removal by index, remember that later elements shift left and a numeric argument chooses the index overload.'],
  ['Use a typed resizable collection.', 'Traverse it safely and explain index shifts after removal.'],
  E(TITLES, 'Count: 2\nOrbit\nMoon\n', ['Read the count and consume its line remainder.', 'Add two full-line titles.', 'size reports two elements.', 'Traversal preserves insertion order.'], '2\nOrbit\nMoon\n'),
  Q('What is the size after these operations?', J('java.util.ArrayList<String> titles = new java.util.ArrayList<>();\ntitles.add("A");\ntitles.add("B");\ntitles.remove(0);\nSystem.out.println(titles.size());'), '1', 'Removing index 0 removes A; B remains at the new index 0.'),
  R('How do arrays and ArrayList differ, and which bounds still apply to get(index)?', 'An array length is fixed; an ArrayList can change its size. A list index must still be nonnegative and below its current size.', ['I distinguish fixed length from resizable size.', 'I state zero-based bounds.', 'I explain that removal shifts later positions.']),
  P('Read a valid n from 0..10, then n full title lines. Store them in ArrayList<String>. Print Count: n and then each title on a separate line, preserving order.', TITLES, [T('two full titles', '2\nThe Long Orbit\nMoon\n', 'Count: 2\nThe Long Orbit\nMoon\n'), T('empty list', '0\n', 'Count: 0\n'), T('duplicate titles permitted', '2\nOrbit\nOrbit\n', 'Count: 2\nOrbit\nOrbit\n')], starter=J('Scanner in = new Scanner(System.in);\n// Read n, consume its remainder, store n full lines, and list them.', SCANNER), rubric=['I use ArrayList<String>, not concatenated text as a fake collection.', 'I preserve insertion order and the empty case.'])),
L('classes-objects', 'Records with Their Own State', 'Construct distinct objects instead of parallel unrelated values.',
  ['A class defines fields and behavior for a kind of object. An object is one instance with its own state. new Item(title, quantity) invokes a constructor to initialize that instance. this.title refers to the field of the current object when a parameter has the same name.',
   'Two distinct new objects have separate fields. Assigning Item b = a copies a reference, not the object. Then a and b refer to the same Item, so changing its mutable quantity through one reference is visible through the other.',
   'For the single-file Studio runner, Item is a static nested class inside Main. That arrangement avoids additional public source files; it does not change Java’s pass-by-value rule. The next lesson controls state through methods.'],
  ['Construct an object with related fields.', 'Distinguish separate instances from two references to one instance.'],
  E(J('Item a = new Item("Orbit", 2);\nItem b = new Item("Moon", 5);\nSystem.out.println(a.title + "|" + a.quantity);\nSystem.out.println(b.title + "|" + b.quantity);', members=ITEM_MEMBERS), 'Orbit|2\nMoon|5\n', ['Each new expression constructs a different object.', 'Each constructor initializes its own fields.', 'Printing one item does not use the other item’s state.']),
  Q('What is printed after the alias updates quantity?', J('Item a = new Item("Orbit", 2);\nItem b = a;\nb.quantity = 7;\nSystem.out.println(a.quantity);', members=ITEM_MEMBERS), '7', 'a and b hold references to the same mutable object.'),
  R('Explain the difference between Item b = a and Item b = new Item("Orbit", 2).', 'The first copies the reference and aliases the same object. The second constructs a distinct object with its own fields.', ['I distinguish reference copying from construction.', 'I describe the visible effect of a mutation through an alias.']),
  P('Read a full title line and then a valid integer quantity line (0..1000). Construct an Item with title and quantity fields via a constructor. Print title|quantity.', J('Scanner in = new Scanner(System.in);\nString title = in.nextLine();\nint quantity = Integer.parseInt(in.nextLine());\nItem item = new Item(title, quantity);\nSystem.out.println(item.title + "|" + item.quantity);', SCANNER, ITEM_MEMBERS), [T('one record', 'Orbit\n3\n', 'Orbit|3\n'), T('zero quantity and spaces', 'Long Orbit\n0\n', 'Long Orbit|0\n')], starter=J('Scanner in = new Scanner(System.in);\n// Read both fields, define Item, construct it, and print its fields.', SCANNER), rubric=['I construct an Item rather than only printing local variables.', 'The constructor stores fields on the current object.'])),
L('encapsulation', 'Keep an Object Valid', 'Put validation next to the state it protects.',
  ['Encapsulation puts a state rule behind an object’s interface. A private quantity field is accessed through getQuantity and updated through setQuantity, which rejects values outside 0..1000 before assigning. A constructor should enforce the same invariant.',
   'A failed update must leave the previous state intact. Validate first, assign second. Do not partially mutate an object and then report an error. A final title reference cannot be reassigned after initialization.',
   'Private access in Java includes the enclosing class’s nestmates; Main can technically access fields of its nested Item. We use getters/setters deliberately here as an interface discipline. In a separate top-level class, unrelated callers cannot directly access those private fields.'],
  ['Protect a state invariant through a method.', 'Preserve the old state when an update is rejected.'],
  E(J('Item item = new Item("Orbit", 2);\nitem.setQuantity(5);\nSystem.out.println(item.getQuantity());', members=PRIVATE_ITEM), '5\n', ['The constructor validates quantity.', 'The setter validates before assignment.', 'The getter exposes the stored value.']),
  Q('What is printed after this rejected update?', J('Item item = new Item("Orbit", 2);\ntry { item.setQuantity(-1); } catch (IllegalArgumentException error) { }\nSystem.out.println(item.getQuantity());', members=PRIVATE_ITEM), '2', 'The setter throws before changing the field, so the old quantity remains.'),
  R('Why must validation happen before field assignment in setQuantity?', 'If the value is rejected after assignment, the object would retain invalid state. Reject first so an exception leaves the previous valid state unchanged.', ['I state the quantity invariant.', 'I place validation before assignment.', 'I explain the old value after failure.']),
  P('Construct an Item with quantity 2. Read one whole-line proposed quantity. Accept 0..1000 with setQuantity and print Updated; otherwise print Invalid. Then print the stored quantity. A failed parse or update must preserve 2.', J('Scanner in = new Scanner(System.in);\nItem item = new Item("Orbit", 2);\ntry {\n    item.setQuantity(Integer.parseInt(in.nextLine().trim()));\n    System.out.println("Updated");\n} catch (IllegalArgumentException error) { System.out.println("Invalid"); }\nSystem.out.println(item.getQuantity());', SCANNER, PRIVATE_ITEM), [T('valid update', '5\n', 'Updated\n5\n'), T('negative rejected', '-1\n', 'Invalid\n2\n'), T('nonnumeric rejected', 'bad\n', 'Invalid\n2\n'), T('zero valid', '0\n', 'Updated\n0\n')], starter=J('Scanner in = new Scanner(System.in);\n// Define a validated Item, attempt the update, then display its retained quantity.', SCANNER), rubric=['The private state is changed through a validated setter.', 'Rejected updates preserve the earlier quantity.'])),
L('inventory-project', 'Milestone: an In-Memory Record Manager', 'Combine objects, a list, methods and command recovery.',
  ['The command format is add|title|quantity, list, or q, one per line. Titles are trimmed, case-sensitive, unique, nonempty and at most 20 UTF-16 code units. Quantities are whole numbers 0..1000. Listing preserves insertion order and prints Empty for no records.',
   'String.split takes a regular expression. To split on a literal |, the Java String must contain an escaped regex separator: split("\\\\|", -1). The -1 retains trailing empty fields so add|Orbit| is recognized as invalid data rather than a different shape.',
   'Use an Item object for each record and ArrayList<Item> for the collection. A find method can return a matching Item or null. Use list and validation methods to keep command parsing from swallowing all the logic.',
   'This milestone stores only in memory: exiting loses the records. The persistence stage adds a documented file format and makes restarting part of the test contract. Do not claim persistence for this version.'],
  ['Build a recoverable multi-command record manager.', 'Represent records as objects and keep responsibilities in small methods.'],
  E(INVENTORY, 'Added\nOrbit|2\nBye\n', ['Parse the add command into three fields.', 'Validate and add one Item.', 'List traverses the current objects.', 'Quit ends the run.'], 'add|Orbit|2\nlist\nq\n'),
  Q('What does the worked manager print for list then q on a fresh run?', INVENTORY, 'Empty\nBye', 'No records have been added in this new in-memory collection.'),
  R('Describe a test sequence that proves duplicate rejection does not erase the original record.', 'Add Orbit with quantity 2, try adding Orbit with quantity 9, then list. Expect Added, Duplicate, and Orbit|2.', ['I state case-sensitive title uniqueness.', 'I keep the first record after a duplicate.', 'I explain that restarting this version loses its in-memory list.']),
  P('Implement the stated add|title|quantity, list, q manager using Item objects, ArrayList<Item> and separate find/list/validation methods. Print Added, Duplicate, Invalid, Unknown, Empty and Bye as applicable. Recognized add with three fields but invalid data → Invalid; other command shapes → Unknown. Stop quietly at EOF.', INVENTORY, [T('normal list', 'add|Orbit|2\nadd|Moon|0\nlist\nq\n', 'Added\nAdded\nOrbit|2\nMoon|0\nBye\n'), T('empty and bad data', 'list\nadd| |3\nadd|Orbit|bad\nadd|Orbit|-1\nq\n', 'Empty\nInvalid\nInvalid\nInvalid\nBye\n'), T('duplicate and malformed command', 'add|Orbit|2\nadd|Orbit|9\nadd|A|B|3\nlist\nq\n', 'Added\nDuplicate\nUnknown\nOrbit|2\nBye\n')], starter=J('Scanner in = new Scanner(System.in);\n// Define Item, find/list/validation methods, then implement the command loop.', SCANNER), hints=['Write the format, uniqueness rule and list order in a test table.', 'Use split with a literal-pipe regex and preserve trailing empty fields.'], rubric=['Records are Item instances in an ArrayList.', 'I separate parsing, validation, searching and listing.', 'Bad requests do not damage the current list.'])),
]
