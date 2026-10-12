import { useEffect, useRef, useState } from 'react'
import { CodeEditor } from './CodeEditor'
import * as api from '../studioApi'
import { downloadText, errorMessage, initialDraft, kindLabel, readLocal, saveLocal } from '../learning'
import type { Assessment, Draft, Reference, RunResult, Task } from '../studioTypes'

export function RunOutput({result}: {result: RunResult}) {
  return <section className="run-output" aria-label="Program Result">
    <div className="section-row"><strong className={result.status==='completed' ? 'positive' : 'negative'}>{result.status.replaceAll('_',' ')}</strong><span className="mono muted">{result.duration_ms !== undefined ? `${result.duration_ms} ms` : ''}</span></div>
    <h4>Standard Output</h4><pre>{result.stdout || '(no output)'}</pre>
    {result.stderr && <><h4>Compiler / Error Output</h4><pre className="error-output">{result.stderr}</pre></>}
    {result.output_truncated && <p className="negative">Output exceeded the capture limit. Reduce repeated output before checking this program.</p>}
    <p className="muted small">A clean run is not a task pass. Use the declared checks to test the requirement.</p>
  </section>
}

export function AssessmentOutput({result}: {result: Assessment}) {
  return <section className={`assessment ${result.passed ? 'assessment-pass' : 'assessment-fail'}`} aria-label="Assessment Feedback" aria-live="polite">
    <div className="section-row"><h3>{result.passed ? result.assisted ? 'Passed with Assistance' : result.assessment==='self_check' ? 'Self-Check Recorded' : 'Checks Passed' : 'Not Yet'}</h3><span className="tag">{result.assessment.replace('_',' ')}</span></div>
    <p>{result.feedback}</p>
    {result.assisted && <p className="callout">This is assisted practice. Start a fresh attempt and solve without hints or the reference to record independent completion.</p>}
    {result.run && <RunOutput result={result.run}/>}
    {!!result.cases.length && <div className="case-results">{result.cases.map((c,index)=><details key={index} open={!c.passed}>
      <summary><span className={c.passed ? 'positive' : 'negative'}>{c.passed ? '✓' : '×'}</span> {c.name} <span className="muted small">{c.status.replaceAll('_',' ')}</span></summary>
      <div className="comparison-grid"><div><h4>Input</h4><pre>{c.stdin || '(empty)'}</pre><h4>Expected Output</h4><pre>{c.expected_stdout || '(no output)'}</pre></div><div><h4>Actual Output</h4><pre>{c.actual_stdout || '(no output)'}</pre>{c.stderr && <pre className="error-output">{c.stderr}</pre>}</div></div>
      {c.files.map(f=><div className="file-check" key={f.name}><strong className={f.passed?'positive':'negative'}>{f.passed?'✓':'×'} {f.name}</strong><div className="comparison-grid"><pre>{f.expected || '(empty file)'}</pre><pre>{f.actual === null ? '(file missing or unreadable)' : f.actual || '(empty file)'}</pre></div></div>)}
    </details>)}</div>}
  </section>
}

interface Props {task: Task; dark: boolean; remote: boolean; onAssessed: () => Promise<void>; onBench: (code: string, stdin: string) => void}

export function TaskPanel({task,dark,remote,onAssessed,onBench}: Props) {
  const localKey=`java-fieldnotes:task:${task.id}`
  const [draft,setDraft]=useState<Draft>(()=>readLocal<Draft>(localKey) ?? initialDraft(task))
  const [ready,setReady]=useState(false)
  const [saving,setSaving]=useState('Loading draft…')
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const [result,setResult]=useState<Assessment|null>(null)
  const [run,setRun]=useState<RunResult|null>(null)
  const [reference,setReference]=useState<Reference|null>(null)
  const [hints,setHints]=useState<string[]>([])
  const [history,setHistory]=useState<Assessment[]|null>(null)
  const [editorKey,setEditorKey]=useState(0)
  const revision=useRef(0)
  const latest=useRef(draft)
  const mounted=useRef(true)
  const requestRef=useRef<{payload:string; id:string}|null>(null)
  latest.current=draft

  useEffect(()=>{
    mounted.current=true
    let active=true
    api.getDraft(task.id).then(saved=>{
      if (!active) return
      const local=readLocal<Draft>(localKey)
      const changedGeneration=!!local && (local.generation ?? 0)!==saved.generation
      if (changedGeneration || !local && (saved.response || saved.code || saved.stdin || saved.assisted || saved.rubric_checks.length)) {
        setDraft({...initialDraft(task,saved.generation),...saved,code:saved.code || initialDraft(task).code}); setEditorKey(k=>k+1)
      } else setDraft(d=>({...d,generation:saved.generation,assisted:d.assisted || saved.assisted}))
      setReady(true)
    }).catch(e=>{ if(active){setReady(true);setError(errorMessage(e))} })
    return ()=>{ active=false; mounted.current=false }
  },[task.id,localKey,task])

  useEffect(()=>{
    if(!ready) return
    const locallySaved=saveLocal(localKey,draft)
    setSaving(locallySaved ? 'Saved in browser · syncing…' : 'Browser storage unavailable · syncing…')
    let active=true
    const timer=setTimeout(()=>api.saveDraft(task.id,draft).then(saved=>{
      if(active && saved.generation===latest.current.generation){setSaving(remote?'Saved to private guest workspace':'Saved locally in SQLite');if(saved.assisted && !draft.assisted) setDraft(d=>d.generation===saved.generation?{...d,assisted:true}:d)}
    }).catch(e=>{if(active && draft.generation===latest.current.generation){setSaving(locallySaved?'Browser draft kept · sync unavailable':'Draft not saved');setError(errorMessage(e))}}),400)
    return ()=>{active=false;clearTimeout(timer)}
  },[draft,ready,localKey,remote,task.id])

  useEffect(()=>()=>{
    if (ready) void api.saveDraft(task.id,latest.current).catch(()=>{})
  },[ready,task.id])

  const update=(patch: Partial<Draft>)=>{revision.current++;setDraft(d=>({...d,...patch}));setResult(null);setRun(null);setError('')}
  const codeTask=['build','repair','modify'].includes(task.kind)
  const assess=async()=>{
    const snapshot={...draft}
    const version=revision.current
    const payload=JSON.stringify(snapshot)
    if(!requestRef.current || requestRef.current.payload!==payload) requestRef.current={payload,id:crypto.randomUUID()}
    setBusy(true);setError('')
    try {
      await api.saveDraft(task.id,snapshot)
      const checked=await api.submitTask(task.id,snapshot,requestRef.current.id)
      await onAssessed()
      if(mounted.current && version===revision.current){setResult(checked);setHistory(null)}
      else if(mounted.current) setError('The assessment was saved for the earlier submitted version. Check your edited draft again.')
    } catch(e){if(mounted.current)setError(errorMessage(e))}
    finally{if(mounted.current)setBusy(false)}
  }
  const runCurrent=async()=>{setBusy(true);setError('');try{const output=await api.runJava(draft.code,draft.stdin);if(mounted.current)setRun(output)}catch(e){if(mounted.current)setError(errorMessage(e))}finally{if(mounted.current)setBusy(false)}}
  const reveal=async()=>{
    if(!window.confirm('Reveal the reference? This marks the current attempt as assisted practice. Your draft will not be replaced.')) return
    setBusy(true);try{const data=await api.getReference(task.id);setReference(data);update({assisted:true})}catch(e){setError(errorMessage(e))}finally{setBusy(false)}
  }
  const hint=async()=>{setBusy(true);try{const data=await api.getHint(task.id,hints.length);setHints(h=>[...h,data.hint]);update({assisted:true})}catch(e){setError(errorMessage(e))}finally{setBusy(false)}}
  const retry=async()=>{
    if(!window.confirm('Start a fresh attempt? Your current draft will reset; saved assessment history stays. Close the reference and solve independently.')) return
    setBusy(true)
    try{const reset=await api.retryTask(task.id);const fresh=initialDraft(task,reset.generation);latest.current=fresh;saveLocal(localKey,fresh);setDraft(fresh);setHints([]);setReference(null);setResult(null);setRun(null);setError('');setEditorKey(k=>k+1);requestRef.current=null;revision.current++}
    catch(e){setError(errorMessage(e))}finally{setBusy(false)}
  }

  return <section className="task-panel" aria-label={`${kindLabel[task.kind]} Task`}>
    <div className="section-row"><div className="eyebrow">{task.required?'Core Requirement':'Transfer Practice'} / {kindLabel[task.kind]}</div><span className={`tag ${draft.assisted?'warning-tag':''}`}>{draft.assisted?'Assisted attempt':'Independent attempt'}</span></div>
    <h3>{kindLabel[task.kind]} the Idea</h3><p className="task-prompt">{task.prompt}</p>
    {task.code && <pre className="source-code" translate="no">{task.code}</pre>}
    {codeTask ? <>
      <p className="muted small" id="editor-instructions">Main.java · {remote ? 'Run/Check sends source to the isolated Java runner; Run sends your input, while Check sends the task test inputs.' : 'Local trusted code only.'} Tab indents; Escape then Tab leaves the editor. Ctrl+Z / Ctrl+Y edits history.</p>
      <CodeEditor value={draft.code} documentKey={editorKey} dark={dark} onChange={code=>update({code})}/>
      <label className="field">Standard Input<textarea name="task-stdin" spellCheck={false} value={draft.stdin} onChange={e=>update({stdin:e.target.value})} rows={4}/></label>
      <details className="declared-tests"><summary>Declared Checks ({task.tests?.length ?? 0} cases)</summary>
        <p className="muted small">Each case starts fresh. Restart steps within a case share files but use separate Java processes. Checks never touch your saved project workspace.</p>
        {task.tests?.map((c,i)=><div className="declared-case" key={i}><h4>{c.name}</h4>{c.files && <p className="small">Initial files: {Object.keys(c.files).join(', ')}</p>}{(c.runs ?? [c]).map((step,j)=><div key={j} className="comparison-grid"><div><span className="muted small">{c.runs ? `Run ${j+1} input` : 'Input'}</span><pre>{step.stdin || '(empty)'}</pre></div><div><span className="muted small">Expected output</span><pre>{step.expected_stdout || '(no output)'}</pre></div></div>)}</div>)}
      </details>
    </> : <label className="field">{task.kind==='predict' ? 'Your Prediction' : 'Your Explanation'}<textarea name="task-response" spellCheck={task.kind==='explain'} value={draft.response} onChange={e=>update({response:e.target.value})} rows={task.kind==='explain'?6:4} placeholder={task.kind==='predict'?'Write the exact answer or output…':'Explain the rule in your own words…'}/></label>}
    {!!task.rubric.length && <fieldset className="rubric"><legend>{codeTask?'Design Self-Check':'Explanation Self-Check'}</legend><p className="muted small">Assess your own work honestly. These criteria are not machine-graded.</p>{task.rubric.map((criterion,index)=><label key={index}><input type="checkbox" checked={draft.rubric_checks[index] ?? false} onChange={e=>{const checks=task.rubric.map((_,i)=>draft.rubric_checks[i] ?? false);checks[index]=e.target.checked;update({rubric_checks:checks})}}/>{criterion}</label>)}</fieldset>}
    {error && <p role="alert" className="inline-error">{error}</p>}
    <div className="action-row"><button className="button primary" onClick={()=>void assess()} disabled={busy || !ready}>{busy?'Working…':codeTask?'Check All Cases':task.kind==='predict'?'Check Prediction':'Record Self-Check'}</button>{codeTask && <button className="button" onClick={()=>void runCurrent()} disabled={busy || !ready}>Run Current Input</button>}<span className="save-state" role="status">{saving}</span></div>
    {run && <RunOutput result={run}/>}
    {result && <AssessmentOutput result={result}/>}
    <div className="practice-tools"><button className="text-button" onClick={()=>void hint()} disabled={busy || hints.length >= (task.hint_count ?? 0)}>Hint {hints.length}/{task.hint_count ?? 0}</button><button className="text-button" onClick={()=>void reveal()} disabled={busy}>Reveal Reference</button><button className="text-button" onClick={()=>void retry()} disabled={busy}>Fresh Attempt</button><button className="text-button" onClick={()=>void api.getHistory(task.id).then(h=>setHistory(h.attempts)).catch(e=>setError(errorMessage(e)))}>Attempt History</button>{codeTask && <><button className="text-button" onClick={()=>onBench(draft.code,draft.stdin)}>Copy Draft to Code Bench</button><button className="text-button" onClick={()=>downloadText('Main.java',draft.code)}>Download Main.java</button></>}</div>
    {!!hints.length && <aside className="hint-box"><h4>Hints Used</h4><ol>{hints.map((h,i)=><li key={i}>{h}</li>)}</ol></aside>}
    {reference && <aside className="reference-box"><h4>Reference · Assisted Practice</h4><p>{reference.explanation}</p>{reference.answer && <pre>{reference.answer}</pre>}{reference.code && <pre className="source-code" translate="no">{reference.code}</pre>}</aside>}
    {history && <div className="history"><h4>Saved Attempts</h4>{history.length===0 ? <p className="muted">No assessed attempts yet. Drafts are saved separately.</p> : <><p className="muted small">Showing {history.length} most recent attempts (up to 50).</p>{history.map(h=><details key={h.attempt_id}><summary>{new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeStyle:'short'}).format(new Date(h.created_at))} · {h.passed?'Passed':'Not yet'} · {h.assisted?'Assisted':'Independent'}</summary>{h.response && <pre>{h.response}</pre>}{h.code && <pre className="source-code">{h.code}</pre>}<AssessmentOutput result={h}/></details>)}</>}</div>}
  </section>
}
