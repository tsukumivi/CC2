import type { ReactNode } from 'react'
import type { ReviewerVisual as ReviewerVisualData } from '../types'

function record(value: unknown): Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : {}
}

function atom(value: unknown): string {
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value)
  const item = record(value)
  for (const key of ['label', 'text', 'name', 'title', 'value', 'description']) {
    if (typeof item[key] === 'string' || typeof item[key] === 'number') return String(item[key])
  }
  return ''
}

function list(value: unknown): unknown[] {
  return Array.isArray(value) ? value : []
}

function textList(value: unknown): string[] {
  return list(value).map(atom).filter(Boolean)
}

function firstText(data: Record<string, unknown>, keys: string[], fallback: string): string {
  for (const key of keys) {
    const value = atom(data[key])
    if (value) return value
  }
  return fallback
}

function Figure({ label, caption, children, variant }: { label: string; caption: string; children: ReactNode; variant: string }) {
  return <figure className={`review-visual review-visual--${variant}`}><div className="review-visual-canvas" role="group" aria-label={label}>{children}</div><figcaption>{caption}</figcaption></figure>
}

export function ReviewerVisual({ visual }: { visual: ReviewerVisualData }) {
  const data = record(visual)
  const kind = typeof data.kind === 'string' ? data.kind : 'flow'
  const caption = firstText(data, ['caption', 'note', 'description', 'title'], 'Use the diagram to explain how the values move or which path is chosen.')

  if (kind === 'memory_slots') {
    const slots = list(data.slots ?? data.memory_slots ?? data.values)
    const resolved = slots.length ? slots : [{ type: 'type', name: 'name', value: 'value' }]
    const labelledSlots = resolved.map(record)
    const isDeclaration = labelledSlots.length > 0 && labelledSlots.every(item => typeof item.label === 'string')
    if (isDeclaration) {
      const fields = Object.fromEntries(labelledSlots.map(item => [atom(item.label).toLowerCase(), atom(item.value)]))
      return <Figure variant="memory" label={`Variable declaration: type ${fields.type || 'unknown'}, name ${fields.name || 'unknown'}, current value ${fields.value || 'unknown'}.`} caption={caption}>
        <span className="review-visual-kicker">READ THE DECLARATION</span>
        <div className="memory-declaration">{(['type', 'name', 'value'] as const).map(key => <div className="memory-declaration-field" key={key}><span>{key === 'value' ? 'CURRENT VALUE' : key.toUpperCase()}</span><strong>{fields[key] || '—'}</strong></div>)}</div>
      </Figure>
    }
    return <Figure variant="memory" label={`Variable memory slots: ${resolved.map(slot => { const item = record(slot); return `${atom(item.type)} ${atom(item.name)} stores ${atom(item.value)}` }).join('; ')}`} caption={caption}>
      <span className="review-visual-kicker">TYPE / NAME / CURRENT VALUE</span>
      <div className="memory-slots">{resolved.map((slot, index) => {
        const item = record(slot)
        return <div className="memory-slot" key={index}><span>{atom(item.type) || 'type'}</span><strong>{atom(item.name) || atom(slot) || 'variable'}</strong><i aria-hidden="true">↓</i><b>{atom(item.value) || '—'}</b></div>
      })}</div>
    </Figure>
  }

  if (kind === 'flow') {
    const steps = list(data.steps ?? data.nodes ?? data.items).map(atom).filter(Boolean)
    const resolved = steps.length ? steps : ['Input', 'Process', 'Output']
    return <Figure variant="flow" label={`Flow: ${resolved.join(', then ')}`} caption={caption}>
      <div className="review-flow-nodes">{resolved.map((step, index) => <div className="review-flow-node-wrap" key={`${step}-${index}`}><div className="review-flow-node"><span>{String(index + 1).padStart(2, '0')}</span><strong>{step}</strong></div>{index < resolved.length - 1 && <span className="review-flow-arrow" aria-hidden="true">→</span>}</div>)}</div>
    </Figure>
  }

  if (kind === 'branch') {
    const condition = firstText(data, ['condition', 'test', 'expression', 'question'], 'Condition?')
    const input = firstText(data, ['input', 'given'], '')
    const route = (keys: string[], fallback: string) => {
      for (const key of keys) {
        const value = data[key]
        const parts = textList(value)
        if (parts.length) return parts.join(' → ')
        const single = atom(value)
        if (single) return single
      }
      return fallback
    }
    const yes = route(['true_path', 'when_true', 'yes', 'true'], 'Condition is true')
    const no = route(['false_path', 'when_false', 'no', 'false'], 'Condition is false')
    const highlight = atom(data.highlight).toLowerCase()
    const trueSelected = ['true', 'yes'].includes(highlight)
    const falseSelected = ['false', 'no'].includes(highlight)
    return <Figure variant="branch" label={`Branching decision${input ? ` for ${input}` : ''}: test ${condition}. If true: ${yes}. If false: ${no}.`} caption={caption}>
      {input && <div className="branch-input"><span>GIVEN</span><strong>{input}</strong></div>}
      <div className="branch-condition"><span>CHECK</span><strong>{condition}</strong></div>
      <div className="branch-routes"><div className={`branch-route branch-route--true${trueSelected ? ' branch-route--selected' : ''}`}><span>{trueSelected ? 'TRUE · SELECTED' : 'TRUE'}</span><strong>{yes}</strong></div><div className={`branch-route branch-route--false${falseSelected ? ' branch-route--selected' : ''}`}><span>{falseSelected ? 'FALSE · SELECTED' : 'FALSE'}</span><strong>{no}</strong></div></div>
    </Figure>
  }

  if (kind === 'switch_routes') {
    const selector = firstText(data, ['selector', 'value', 'input'], 'choice')
    const routes = list(data.routes ?? data.cases ?? data.options)
    const resolved = routes.length ? routes : [{ case: 'case 1', output: 'Matching route' }, { case: 'default', output: 'Fallback route' }]
    return <Figure variant="switch" label={`Switch routes from ${selector}: ${resolved.map(route => { const item = record(route); return `case ${atom(item.case) || atom(item.label)} leads to ${atom(item.output) || atom(item.result)}` }).join('; ')}`} caption={caption}>
      <div className="switch-selector"><span>SELECTOR</span><strong>{selector}</strong></div>
      <div className="switch-routes">{resolved.map((route, index) => {
        const item = record(route)
        const routeName = atom(item.case ?? item.label) || `case ${index + 1}`
        const output = atom(item.output ?? item.result ?? item.action) || 'Run this case'
        return <div className={`switch-route ${routeName.toLowerCase() === 'default' ? 'switch-route--default' : ''}`} key={`${routeName}-${index}`}><span>{routeName === 'default' ? 'DEFAULT' : `CASE ${routeName}`}</span><strong>{output}</strong></div>
      })}</div>
    </Figure>
  }

  if (kind === 'calculation_flow') {
    const steps = textList(data.steps)
    if (steps.length) {
      return <Figure variant="calculation" label={`Calculation trace: ${steps.join('; then ')}`} caption={caption}>
        <span className="review-visual-kicker">TRACE THE VALUES</span>
        <ol className="calculation-steps">{steps.map((step, index) => <li key={`${step}-${index}`}><span>{String(index + 1).padStart(2, '0')}</span><strong>{step}</strong></li>)}</ol>
      </Figure>
    }
    const operands = list(data.operands ?? data.inputs ?? data.values).map(atom).filter(Boolean)
    const left = operands[0] || firstText(data, ['left'], '15')
    const right = operands[1] || firstText(data, ['right'], '2')
    const operator = firstText(data, ['operator'], '÷')
    const result = firstText(data, ['result', 'output'], '7')
    return <Figure variant="calculation" label={`Calculation: ${left} ${operator} ${right} gives ${result}.`} caption={caption}>
      <span className="review-visual-kicker">FOLLOW EACH OPERATION</span>
      <div className="calculation-flow"><span>{left}</span><i aria-hidden="true">{operator}</i><span>{right}</span><i aria-hidden="true">=</i><strong>{result}</strong></div>
    </Figure>
  }

  const fallback = firstText(data, ['caption', 'description', 'text', 'title'], 'Visual model for this concept.')
  return <Figure variant="flow" label={fallback} caption={fallback}><div className="review-flow-node"><span>01</span><strong>{fallback}</strong></div></Figure>
}
