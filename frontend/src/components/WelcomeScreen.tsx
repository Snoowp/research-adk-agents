import { InputForm } from "./InputForm";
import cegekaLogo from "../assets/images/cegeka-logo.png";

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
      <div className="flex items-center justify-center gap-4 mb-6 animate-fadeIn">
        <img 
          src={cegekaLogo} 
          alt="Cegeka Logo" 
          className="h-12 w-12 md:h-16 md:w-16 object-contain animate-slideInRight"
        />
        <h1 className="text-5xl md:text-6xl font-bold text-cegeka-primary animate-fadeIn animation-delay-200">
          Research Agent
        </h1>
      </div>
      <p className="text-xl md:text-2xl text-muted-foreground animate-fadeIn animation-delay-200">
        Hoe kan ik je vandaag helpen met onderzoek?
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
        Mogelijk gemaakt door <span className="text-cegeka-primary font-semibold">Google Agent Development Kit (ADK)</span>
      </p>
      <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
        <span className="status-indicator status-running"></span>
        Geavanceerd onderzoek met iteratieve verfijning
      </div>
    </div>
  </div>
);