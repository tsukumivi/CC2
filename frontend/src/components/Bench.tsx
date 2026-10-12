import { useEffect, useRef, useState } from 'react'
import * as api from '../studioApi'
import { downloadText, errorMessage, readLocal, saveLocal } from '../learning'
import { CodeEditor } from './CodeEditor'
import { RunOutput } from './TaskPanel'
import type { Project, ProjectFile, RunResult } from '../studioTypes'

export const BLANK_SOURCE='public class Main {\n    public static void main(String[] args) {\n        // Build something useful.\n    }\n}\n'
export interface BenchDraft {code: string; stdin: string; project_id?: string; title: string; description: string}
export const BENCH_KEY='java-fieldnotes:bench'

export function Bench({dark,projectId,remote,onProjectSaved}: {dark:boolean;projectId:string;remote:boolean;onProjectSaved:(project:Project)=>void}) {
  const [draft,setDraft]=useState<BenchDraft>(()=>readLocal<BenchDraft>(BENCH_KEY) ?? {code:BLANK_SOURCE,stdin:'',title:'Untitled Project',description:''})
  const [key,setKey]=useState(0)
  const [busy,setBusy]=useState(false)
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState('')
  const [message,setMessage]=useState('')
  const [result,setResult]=useState<RunResult|null>(null)
  const [files,setFiles]=useState<ProjectFile[]>([])
  const [fileName,setFileName]=useState('records.txt')
  const [fileContent,setFileContent]=useState('')
  const [fileLoaded,setFileLoaded]=useState(false)
  const [persistedCode,setPersistedCode]=useState<string|null>(null)
  const revision=useRef(0)
  const mounted=useRef(true)
  const latest=useRef(draft);latest.current=draft
  const activeId=draft.project_id
  const changed=activeId && persistedCode!==null && draft.code!==persistedCode
  const refreshFiles=async(id: string)=>{const data=await api.getFiles(id);if(mounted.current && latest.current.project_id===id){setFiles(data.files);if(data.truncated)setMessage('File listing stopped after 200 entries. Inspect the workspace locally.')}}

  useEffect(()=>{mounted.current=true;return()=>{mounted.current=false}},[])
  useEffect(()=>{
    let current=true
    if(projectId && projectId!==draft.project_id){
      setLoading(true)
      api.getProject(projectId).then(p=>{
        if(current){setDraft(d=>({...d,code:p.code,title:p.title,description:p.description,project_id:p.id}));setPersistedCode(p.code);setKey(k=>k+1);setResult(null);setFileLoaded(false);setMessage('Opened saved project and its persistent data workspace.')}
      }).catch(e=>{if(current)setError(errorMessage(e))}).finally(()=>{if(current)setLoading(false)})
    } else if(draft.project_id) api.getProject(draft.project_id).then(p=>{if(current)setPersistedCode(p.code)}).catch(e=>{if(current)setError(errorMessage(e))})
    return()=>{current=false}
    // The route, not every draft edit, controls opening a different saved project.
  },[projectId])
  useEffect(()=>{if(!saveLocal(BENCH_KEY,draft))setError('Browser storage is full. Save the project or download Main.java before leaving.')},[draft])
  useEffect(()=>{setFiles([]);if(activeId)void refreshFiles(activeId).catch(e=>setError(errorMessage(e)))},[activeId])
  useEffect(()=>{
    const warn=(event:BeforeUnloadEvent)=>{if(changed){event.preventDefault();event.returnValue=''}}
    window.addEventListener('beforeunload',warn);return()=>window.removeEventListener('beforeunload',warn)
  },[changed])
  const update=(patch:Partial<BenchDraft>)=>{revision.current++;setDraft(d=>({...d,...patch}));setResult(null);setError('');setMessage('')}
  const run=async()=>{
    const snapshot={...draft};const version=revision.current
    setBusy(true);setError('');setResult(null)
    try{const output=await api.runJava(snapshot.code,snapshot.stdin,snapshot.project_id);if(mounted.current && version===revision.current)setResult(output);else if(mounted.current)setMessage('The earlier submitted version finished. Run the edited version to see its output.');if(snapshot.project_id)await refreshFiles(snapshot.project_id)}
    catch(e){if(mounted.current)setError(errorMessage(e))}finally{if(mounted.current)setBusy(false)}
  }
  const save=async(copy=false)=>{
    const snapshot={...draft};const version=revision.current
    setBusy(true);setError('')
    try{
      const p=await api.saveProject({id:copy?undefined:snapshot.project_id,title:snapshot.title,description:snapshot.description,code:snapshot.code})
      const readBack=await api.getProject(p.id!)
      if(readBack.code!==snapshot.code)throw new Error('Saved source could not be verified. Keep your browser draft and retry.')
      if(mounted.current){setDraft(d=>({...d,project_id:p.id}));setPersistedCode(snapshot.code);setMessage(version===revision.current ? copy?'Saved as a new project. Its data workspace starts empty.':'Project saved and verified. Data files stay in its workspace.':'Earlier source version saved. Your newer browser draft is still unsaved.');onProjectSaved(p)}
    }catch(e){if(mounted.current)setError(errorMessage(e))}finally{if(mounted.current)setBusy(false)}
  }
  const fresh=()=>{if(!window.confirm('Start a new scratch program? The current browser draft will be replaced. Saved projects and their data files stay.'))return;setDraft({code:BLANK_SOURCE,stdin:'',title:'Untitled Project',description:''});setPersistedCode(null);setKey(k=>k+1);setResult(null);setFiles([]);setFileLoaded(false);setMessage('New scratch program. Save a project before testing persistent files.')}
  const readFile=async(name:string)=>{if(!activeId)return;setBusy(true);try{const f=await api.getFile(activeId,name);setFileName(name);setFileContent(f.content);setFileLoaded(true)}catch(e){setError(errorMessage(e))}finally{setBusy(false)}}
  const writeFile=async()=>{
    if(!activeId)return
    if(!window.confirm(`Replace ${fileName} in this project with the text shown? Export a backup first if you need its old content.`))return
    setBusy(true);setError('')
    try{await api.putFile(activeId,fileName,fileContent);const actual=await api.getFile(activeId,fileName);if(actual.content!==fileContent)throw new Error('File content did not match after saving.');setFileLoaded(true);setMessage('Data file saved and read-back verified.');await refreshFiles(activeId)}catch(e){setError(errorMessage(e))}finally{setBusy(false)}
  }
  const removeFile=async(name:string)=>{if(!activeId || !window.confirm(`Delete ${name} from this project? This cannot be undone.`))return;setBusy(true);try{await api.deleteFile(activeId,name);await refreshFiles(activeId);setFileLoaded(false);setMessage('Data file deleted.')}catch(e){setError(errorMessage(e))}finally{setBusy(false)}}

  return <div className="bench-layout">
    <section className="panel bench-main"><div className="section-row"><span className="eyebrow">Main.java / Code Bench</span><span className={`tag ${activeId?'positive-tag':''}`}>{activeId?'Saved-Project Workspace':'Temporary Scratch Run'}</span></div>
      <p className="callout small">{remote ? 'When you run code, its source, standard input, and this project’s data files are sent to SandboxAPI through RapidAPI for isolated Java 21 execution. Do not include passwords, API keys, or personal information. The shared site has a 500-run monthly free-tier limit.' : 'Java runs on your computer, not in a security sandbox. Run only code you trust. The JVM can access your files and network.'}</p>
      {loading && <p role="status">Opening project…</p>}
      <p id="editor-instructions" className="muted small">Ctrl+Z / Ctrl+Y edits history. Escape then Tab leaves the editor. Input below is a finite batch, not a live prompt.</p>
      <CodeEditor value={draft.code} documentKey={key} dark={dark} onChange={code=>update({code})}/>
      <label className="field">Standard Input<textarea name="bench-stdin" value={draft.stdin} onChange={e=>update({stdin:e.target.value})} spellCheck={false} rows={5}/></label>
      <div className="action-row"><button className="button primary" onClick={()=>void run()} disabled={busy || loading}>{busy?'Working…':'Compile & Run'}</button><button className="button" onClick={()=>downloadText('Main.java',draft.code)}>Download Main.java</button><button className="text-button" onClick={fresh} disabled={busy}>New Scratch</button></div>
      {result && <RunOutput result={result}/>}
      {error && <p role="alert" className="inline-error">{error}</p>}{message && <p role="status" className="callout">{message}</p>}
    </section>
    <aside className="bench-side"><section className="panel"><h2>Keep Your Work</h2><p className="muted small">{remote ? 'Browser drafts survive navigation. Save source to your private guest workspace in Cloudflare D1. The guest cookie keeps this browser profile connected; it does not sync across devices.' : 'Browser drafts survive navigation. Save source to SQLite to keep a named project and its data workspace.'}</p>
      <label className="field">Project Title<input name="project-title" autoComplete="off" value={draft.title} maxLength={120} onChange={e=>update({title:e.target.value})}/></label>
      <label className="field">Project Notes<textarea name="project-notes" value={draft.description} maxLength={1000} rows={3} onChange={e=>update({description:e.target.value})}/></label>
      <div className="action-row"><button className="button primary" onClick={()=>void save()} disabled={busy || loading}>{activeId?'Save Project':'Save New Project'}</button>{activeId && <button className="button" onClick={()=>void save(true)} disabled={busy}>Save a Copy</button>}</div>
      <p className="save-state">{changed?'Source changed · save needed':activeId?'Source saved · browser draft kept':'Scratch source kept in this browser'}</p>
    </section><section className="panel"><h2>Project Data</h2>{!activeId?<p className="muted">Save a project first. Scratch files are deleted after each run.</p>:<>
      <p className="muted small">These files survive separate runs of this saved project. Task-check fixtures are separate. Text import/export limit: 64 KB per file.</p>
      <button className="text-button" onClick={()=>void refreshFiles(activeId).catch(e=>setError(errorMessage(e)))} disabled={busy}>Refresh Files</button>
      {files.length===0?<p className="muted small">No data files yet. Run your saved program or import one below.</p>:<ul className="file-list">{files.map(f=><li key={f.name}><button className="text-button" onClick={()=>void readFile(f.name)} disabled={!f.readable || busy}>{f.name}</button><span className="muted small">{new Intl.NumberFormat().format(f.bytes)} B</span><button className="text-button danger" aria-label={`Delete ${f.name}`} onClick={()=>void removeFile(f.name)} disabled={busy}>Delete</button></li>)}</ul>}
      <label className="field">Data Filename<input name="data-filename" autoComplete="off" value={fileName} onChange={e=>{setFileName(e.target.value);setFileLoaded(false)}} placeholder="records.txt…"/></label>
      <label className="field">UTF-8 Data<textarea name="file-content" value={fileContent} spellCheck={false} rows={6} onChange={e=>setFileContent(e.target.value)}/></label>
      <div className="action-row"><button className="button" onClick={()=>void writeFile()} disabled={busy}>Save Data File</button><button className="button" onClick={()=>downloadText(fileName,fileContent)} disabled={!fileLoaded}>Export Data</button></div>
      <label className="field small">Import a Local Text File<input type="file" name="import-data" accept=".txt,.csv,.json,.md,.log,.dat" onChange={e=>{const f=e.target.files?.[0];if(!f)return;if(f.size>64000){setError('File exceeds the 64 KB import limit.');return}void f.text().then(text=>{setFileName(f.name);setFileContent(text);setFileLoaded(false)})}}/></label><p className="muted small">Import loads text into the editor only. Save Data File confirms any replacement.</p>
    </>}</section><section className="panel"><h2>Outside the Studio</h2><p className="muted small">Download Main.java and export any data files. In that same folder:</p><pre>javac --release 21 -encoding UTF-8 Main.java{'\n'}java -Dfile.encoding=UTF-8 Main</pre><p className="muted small">Keep the same working directory when testing restart persistence.</p></section></aside>
  </div>
}
