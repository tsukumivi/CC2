import type { Concept, FlexibleText } from '../types'

function textOf(value: FlexibleText): string {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.map(String).join(' ')
  if (value && typeof value === 'object') {
    for (const key of ['description', 'text', 'label', 'title', 'type']) {
      const picked = value[key]
      if (typeof picked === 'string') return picked
    }
  }
  return ''
}

const modelSteps: Record<string, { nodes: string[]; caption: string }> = {
  'read-input': { nodes: ['Keyboard', 'Scanner', 'Variable'], caption: 'A value travels from the prompt into a typed variable.' },
  'types-variables': { nodes: ['Type', 'Name', 'Value'], caption: 'A declaration labels a storage box with a type, a name, and a current value.' },
  'arithmetic-integer-division': { nodes: ['Values', 'Operators', 'Result'], caption: 'Follow each operation in order; parentheses make the order visible.' },
  'comparisons-strings': { nodes: ['Values', 'Compare', 'true / false'], caption: 'A comparison reduces information to a boolean decision.' },
  'if-else-branches': { nodes: ['Condition', 'true path', 'false path'], caption: 'Only the path selected by the condition runs.' },
  'switch-selection': { nodes: ['Choice', 'Matching case', 'Output'], caption: 'One value selects a matching case; default catches everything else.' },
  'validation-methods': { nodes: ['Input', 'Valid?', 'Continue / return'], caption: 'A guard checks an invalid case first and returns before the normal path.' },
  'workflow-projects': { nodes: ['Input', 'Validate', 'Calculate', 'Output'], caption: 'A useful program connects small steps into one traceable flow.' },
}

export function VisualModel({ concept }: { concept: Concept }) {
  const model = modelSteps[concept.id] ?? {
    nodes: concept.source_concepts?.slice(0, 4) ?? ['Input', 'Process', 'Output'],
    caption: textOf(concept.visual) || 'Follow the information as it moves through this concept.',
  }

  const branching = concept.id === 'if-else-branches' || concept.id === 'comparisons-strings' || concept.id === 'validation-methods'

  return (
    <figure className="model-figure">
      <div className={`model-map ${branching ? 'model-map--branch' : ''}`} role="img" aria-label={`${concept.title} model: ${model.nodes.join(', then ')}`}>
        {model.nodes.map((node, index) => (
          <div className="model-node-wrap" key={`${node}-${index}`}>
            <div className={`model-node ${branching && index > 0 ? (index === 1 ? 'model-node--yes' : 'model-node--no') : ''}`}>
              <span className="model-index">{String(index + 1).padStart(2, '0')}</span>
              <span>{node}</span>
            </div>
            {index < model.nodes.length - 1 && <span className="model-arrow" aria-hidden="true">{branching && index === 0 ? '↙  ↘' : '→'}</span>}
          </div>
        ))}
      </div>
      <figcaption>{model.caption}</figcaption>
    </figure>
  )
}

