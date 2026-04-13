export function TasksPage() {
  return (
    <section>
      <header className="page-header">
        <span className="eyebrow">Execution</span>
        <h2>Tasks</h2>
        <p>Task center placeholder for watching, near-trigger, and ready actions.</p>
      </header>

      <div className="panel-grid single-column">
        <article className="panel">
          <h3>Ready to Execute</h3>
          <p>No generated tasks yet. Backend task planner will populate this view.</p>
        </article>
      </div>
    </section>
  );
}

