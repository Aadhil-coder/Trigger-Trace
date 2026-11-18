export default function SafetyNotice({ onAccept }) {
  return (
    <div className="safety-screen">
      <div className="safety-card">
        <h1>Before you start</h1>

        <p>
          <strong>During a severe attack, use your inhaler and follow your asthma action plan,
          or call emergency services first.</strong> Log the attack afterwards.
        </p>

        <ul>
          <li>TriggerTrace finds <strong>possible patterns</strong>. It does not diagnose and does not give treatment advice.</li>
          <li>Patterns are not causes. Discuss them with your doctor.</li>
          <li>The demo uses <strong>synthetic data</strong>. No real patient records are used.</li>
          <li>Only your district is stored, not your exact location.</li>
        </ul>

        <button className="btn btn-primary btn-block" onClick={onAccept}>
          I understand
        </button>
      </div>
    </div>
  );
}