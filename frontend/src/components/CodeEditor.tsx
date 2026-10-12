import { useEffect, useRef, useState } from 'react'
import { basicSetup, EditorView } from 'codemirror'
import { Compartment } from '@codemirror/state'
import { keymap } from '@codemirror/view'
import { indentWithTab, redo, redoDepth, undo, undoDepth } from '@codemirror/commands'
import { java } from '@codemirror/lang-java'
import { oneDark } from '@codemirror/theme-one-dark'

interface CodeEditorProps {
  value: string
  documentKey: number
  dark: boolean
  onChange: (value: string) => void
}

export function CodeEditor({ value, documentKey, dark, onChange }: CodeEditorProps) {
  const hostRef = useRef<HTMLDivElement>(null)
  const viewRef = useRef<EditorView | null>(null)
  const themeRef = useRef(new Compartment())
  const changeRef = useRef(onChange)
  const [history, setHistory] = useState({ undo: 0, redo: 0 })
  changeRef.current = onChange

  useEffect(() => {
    if (!hostRef.current) return
    const view = new EditorView({
      doc: value,
      extensions: [
        basicSetup,
        java(),
        themeRef.current.of(dark ? oneDark : []),
        keymap.of([indentWithTab]),
        EditorView.lineWrapping,
        EditorView.contentAttributes.of({ 'aria-label': 'Java source code', 'aria-multiline': 'true', 'aria-describedby': 'editor-instructions' }),
        EditorView.updateListener.of(update => {
          if (update.docChanged) {
            changeRef.current(update.state.doc.toString())
            setHistory({ undo: undoDepth(update.state), redo: redoDepth(update.state) })
          }
        }),
        EditorView.theme({
          '&': { fontSize: '13px', minHeight: '320px', backgroundColor: 'var(--bg-input)', color: 'var(--text)' },
          '.cm-scroller': { fontFamily: 'var(--font-mono)', lineHeight: '1.7', overflow: 'auto' },
          '.cm-gutters': { backgroundColor: 'var(--bg-panel)', borderRight: '1px solid var(--line-strong)' },
          '.cm-activeLine': { backgroundColor: 'var(--lavender-dim)' },
          '.cm-cursor': { borderLeftColor: 'var(--gold-bright)' },
        }),
      ],
      parent: hostRef.current,
    })
    viewRef.current = view
    setHistory({ undo: undoDepth(view.state), redo: redoDepth(view.state) })
    return () => {
      view.destroy()
      viewRef.current = null
    }
    // Only explicit document loads reset history; theme changes reconfigure.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentKey])

  useEffect(() => {
    viewRef.current?.dispatch({effects: themeRef.current.reconfigure(dark ? oneDark : [])})
  }, [dark])

  return <div className="code-editor-shell">
    <div className="editor-history-actions" role="group" aria-label="Code editing history">
      <button type="button" className="editor-history-button" onClick={() => { if (viewRef.current) undo(viewRef.current) }} disabled={history.undo === 0} aria-label="Undo last change" title="Undo (Ctrl+Z)"><span aria-hidden="true">↶</span>Undo</button>
      <button type="button" className="editor-history-button" onClick={() => { if (viewRef.current) redo(viewRef.current) }} disabled={history.redo === 0} aria-label="Redo last undone change" title="Redo (Ctrl+Y)" ><span aria-hidden="true">↷</span>Redo</button>
      <span className="editor-history-hint">Ctrl+Z / Ctrl+Y</span>
    </div>
    <div className="code-editor" ref={hostRef} aria-label="Java code editor" />
  </div>
}
