interface ProgressBarProps {
  progress: number; // 0-100
  label?: string;
  showPercentage?: boolean;
}

function ProgressBar({ progress, label, showPercentage = true }: ProgressBarProps) {
  // Ensure progress is between 0 and 100
  const normalizedProgress = Math.min(Math.max(progress, 0), 100);

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between mb-2">
          <span className="text-sm text-slate-300">{label}</span>
          {showPercentage && (
            <span className="text-sm text-slate-400">{normalizedProgress}%</span>
          )}
        </div>
      )}
      <div className="w-full bg-slate-700/50 rounded-full h-2.5 overflow-hidden">
        <div
          className="bg-gradient-to-r from-blue-500 to-blue-400 h-2.5 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${normalizedProgress}%` }}
        >
          {/* Animated shimmer effect */}
          <div className="w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
        </div>
      </div>
    </div>
  );
}

export default ProgressBar;
