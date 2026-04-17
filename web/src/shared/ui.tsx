import { PropsWithChildren, ReactNode } from "react";

type Tone = "default" | "positive" | "warning" | "danger";

export function StatCard(props: {
  label: string;
  value: ReactNode;
  note: ReactNode;
  tone?: Tone;
}) {
  const toneClass = props.tone ? ` stat-card-${props.tone}` : "";

  return (
    <article className={`panel stat-card${toneClass}`}>
      <p className="stat-label">{props.label}</p>
      <p className="metric metric-compact">{props.value}</p>
      <p className="panel-note">{props.note}</p>
    </article>
  );
}

export function PageSection(props: PropsWithChildren<{ title: string; description?: ReactNode; actions?: ReactNode }>) {
  return (
    <section className="section-block">
      <div className="section-header">
        <div>
          <h3>{props.title}</h3>
          {props.description ? <p className="panel-note">{props.description}</p> : null}
        </div>
        {props.actions ? <div className="section-actions">{props.actions}</div> : null}
      </div>
      {props.children}
    </section>
  );
}

export function KeyValueList(props: { items: Array<{ label: string; value: ReactNode; tone?: Tone }> }) {
  return (
    <div className="kv-list">
      {props.items.map((item) => (
        <div key={item.label} className="kv-row">
          <span className="kv-label">{item.label}</span>
          <span className={`kv-value${item.tone ? ` value-${toneToClass(item.tone)}` : ""}`}>{item.value}</span>
        </div>
      ))}
    </div>
  );
}

function toneToClass(tone: Tone) {
  switch (tone) {
    case "positive":
      return "positive";
    case "warning":
      return "warning";
    case "danger":
      return "negative";
    case "default":
    default:
      return "neutral";
  }
}
