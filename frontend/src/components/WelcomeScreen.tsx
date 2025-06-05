import { InputForm } from "./InputForm";

interface WelcomeScreenProps {
  handleSubmit: (
    submittedInputValue: string,
    effort: string,
    model: string
  ) => void;
  onCancel: () => void;
  isLoading: boolean;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  handleSubmit,
  onCancel,
  isLoading,
}) => (
  <div className="flex flex-col items-center justify-center text-center px-4 flex-1 w-full max-w-3xl mx-auto gap-6 animate-fadeInUp">
    <div className="space-y-4">
      <h1 className="text-5xl md:text-6xl font-bold text-cegeka-primary mb-3 animate-fadeIn">
        Research Agent
      </h1>
      <p className="text-xl md:text-2xl text-muted-foreground animate-fadeIn animation-delay-200">
        How can I help you research today?
      </p>
    </div>
    <div className="w-full mt-6 animate-fadeInUp animation-delay-400">
      <InputForm
        onSubmit={handleSubmit}
        isLoading={isLoading}
        onCancel={onCancel}
        hasHistory={false}
      />
    </div>
    <div className="text-center space-y-2 animate-fadeIn animation-delay-600">
      <p className="text-sm text-muted-foreground">
        Powered by <span className="text-cegeka-primary font-semibold">Google Agent Development Kit (ADK)</span>
      </p>
      <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
        <span className="status-indicator status-running"></span>
        Advanced research with iterative refinement
      </div>
    </div>
  </div>
);