export function PortfolioPage() {
  return (
    <section>
      <header className="page-header">
        <span className="eyebrow">IBKR</span>
        <h2>Portfolio</h2>
        <p>Account snapshot, cash, holdings, and unrealized P/L will render here.</p>
      </header>

      <div className="panel-grid">
        <article className="panel">
          <h3>Account Value</h3>
          <p>--</p>
        </article>
        <article className="panel">
          <h3>Available Cash</h3>
          <p>--</p>
        </article>
      </div>
    </section>
  );
}

