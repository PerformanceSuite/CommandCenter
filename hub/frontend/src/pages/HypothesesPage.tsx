import { HypothesisDashboard } from '../components/HypothesisDashboard';

export function HypothesesPage() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-white">Hypothesis Validation</h2>
        <p className="text-slate-400 mt-1">
          Validate business hypotheses using multi-model AI debates
        </p>
      </div>
      <HypothesisDashboard />
    </div>
  );
}

export default HypothesesPage;
