export default function SafetyNotice({ onAccept }) {
  return (
    <main className="safety-screen">
      <section className="safety-card" aria-labelledby="safety-title">
        <h1 id="safety-title">Safety notice</h1>
        <p>
          TriggerTrace helps you record asthma attacks and notice patterns. It
          does not provide medical advice or replace care from a healthcare
          professional.
        </p>
        <p>
          During a severe attack, follow your asthma action plan or call
          emergency services first. Do not delay treatment to use this app.
        </p>
        <button className="btn btn-primary btn-block" onClick={onAccept}>
          I understand, continue
        </button>
      </section>
    </main>
  );
}
