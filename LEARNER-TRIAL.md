# Learner Trial — Practical Java Fieldnotes

**Status: not run.** Automated implementation checks are not evidence of educational effectiveness. No learner results or success rates are asserted here.

## Questions

1. Can a new learner explain what the compiler and JVM do, then write a small program without copying the worked example?
2. Do failed checks lead to a useful correction rather than random edits or answer copying?
3. After finishing a stage, can the learner solve its optional transfer program in a new domain?
4. After the persistence stage, can the learner build and export a record manager, handle corrupt input/data, and demonstrate a real restart?
5. Does a delayed task still work without hints or the original solution?

## Safe setup

Use a separate learner-trial data directory, never production or automated QA storage. Record which course revision was used. Keep source, attempt evidence and the learner's consent; do not upload personal work or record credentials. Explain that self-check boxes require honest judgment and that reference use is allowed but recorded as assistance.

## First-success pilot

Start with `java-program-skeleton` and `output-and-comments`. Let the learner use the explanation and worked example. Observe the first prediction, explanation self-check and independent build. Do not rescue a compiler error immediately: ask the learner what the diagnostic points to and let them attempt a correction.

Then close the example. Ask for a new two-line greeting program with different text and one comment. Run its source, inspect output and ask for an explanation of source versus bytecode. This is a human-observed transfer task, not a fabricated automated score.

Record: time to first successful run; error encountered; whether the diagnostic was understood; hints/references used; source before and after correction; whether the learner can explain the result. An app pass alone is insufficient.

## Stage transfer and delayed revisit

At the end of each stage, use the marked optional transfer program. The learner should write from its requirement, not copy the reference. Keep failed and successful attempts. Distinguish output-case success from the learner-confirmed structural rubric.

On a later session, present a fresh variation in the same skill. Do not show the old solution first. Record the time gap, assistance and new source. If the learner needs help, record that rather than relabeling the attempt independent.

## Capstone trial

After the prerequisite route, start a fresh capstone attempt. Ask the learner to plan requirements, implement separate methods and record objects, and test ordinary, boundary and invalid inputs. They must show:

- Add, update, remove and list behavior, including invalid commands/quantities.
- UTF-8 save and load; a separate JVM reads previously saved data.
- Missing/corrupt data behavior without silent destruction of the corrupt file.
- A documented format and a small requirement-to-test table.
- Exported `Main.java` compiling/running outside the Studio, with data exported separately.

Observe one new requirement change, such as a different quantity bound. Ask which validation, test and documentation must change. Do not claim professional readiness from this task.

## Record sheet

| Item | Observation (leave blank until observed) |
|---|---|
| Course revision / date / learner consent | |
| Prior Java experience | |
| Lesson / transfer task | |
| First-attempt source and result | |
| Diagnostic understood? Evidence | |
| Assistance used | |
| Corrected source and actual result | |
| Rubric explanation in learner's own words | |
| Delayed revisit interval and result | |
| UI/content friction and proposed fix | |

## Interpretation

A successful pilot supports usability for that learner and those tasks, not general educational efficacy. Treat repeated confusion, excessive answer copying, unexplained passes and failed delayed transfer as redesign evidence. Revise the specific explanation, scaffold or feedback involved, then repeat with a fresh task. Report actual observations; never fill missing outcomes with synthetic learner data.
