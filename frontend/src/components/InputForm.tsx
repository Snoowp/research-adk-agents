import { useState } from "react";
import { Button } from "@/components/ui/button";
import { SquarePen, Brain, Send, StopCircle, Zap, Cpu } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Updated InputFormProps
interface InputFormProps {
  onSubmit: (inputValue: string, effort: string, model: string) => void;
  onCancel: () => void;
  isLoading: boolean;
  hasHistory: boolean;
}

export const InputForm: React.FC<InputFormProps> = ({
  onSubmit,
  onCancel,
  isLoading,
  hasHistory,
}) => {
  const [internalInputValue, setInternalInputValue] = useState("");
  const [effort, setEffort] = useState("medium");
  const [model, setModel] = useState("gemini-2.5-flash-preview-04-17");

  const handleInternalSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!internalInputValue.trim()) return;
    onSubmit(internalInputValue, effort, model);
    setInternalInputValue("");
  };

  const handleInternalKeyDown = (
    e: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleInternalSubmit();
    }
  };

  const isSubmitDisabled = !internalInputValue.trim() || isLoading;

  return (
    <form
      onSubmit={handleInternalSubmit}
      className={`flex flex-col gap-3 p-3 `}
    >
      <div
        className={`flex flex-row items-center justify-between text-foreground rounded-3xl break-words min-h-7 bg-card border border-border px-4 pt-3 shadow-sm`}
      >
        <Textarea
          value={internalInputValue}
          onChange={(e) => setInternalInputValue(e.target.value)}
          onKeyDown={handleInternalKeyDown}
          placeholder="Wat wil je vandaag onderzoeken?"
          className={`w-full text-foreground placeholder-muted-foreground resize-none border-0 focus:outline-none focus:ring-0 outline-none focus-visible:ring-0 shadow-none 
                        md:text-base min-h-[56px] max-h-[200px] bg-transparent`}
          rows={1}
        />
        <div className="-mt-3">
          {isLoading ? (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="text-cegeka-secondary hover:text-cegeka-secondary/80 hover:bg-cegeka-secondary/10 p-2 cursor-pointer rounded-full transition-all duration-200"
              onClick={onCancel}
            >
              <StopCircle className="h-5 w-5" />
            </Button>
          ) : (
            <Button
              type="submit"
              className={`btn-cegeka-primary ${
                isSubmitDisabled
                  ? "opacity-50 cursor-not-allowed"
                  : ""
              } text-base rounded-full px-4 py-2`}
              disabled={isSubmitDisabled}
            >
              Research
            </Button>
          )}
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="flex flex-row gap-2">
          <div className="flex flex-row gap-2 bg-card border border-border text-foreground focus:ring-primary rounded-xl pl-2 max-w-[100%] sm:max-w-[90%]">
            <div className="flex flex-row items-center text-sm text-muted-foreground">
              <Brain className="h-4 w-4 mr-2 text-cegeka-accent" />
              Inspanning
            </div>
            <Select value={effort} onValueChange={setEffort}>
              <SelectTrigger className="w-[120px] bg-transparent border-none cursor-pointer">
                <SelectValue placeholder="Inspanning" />
              </SelectTrigger>
              <SelectContent className="bg-card border-border text-foreground cursor-pointer shadow-lg">
                <SelectItem
                  value="low"
                  className="hover:bg-accent focus:bg-accent cursor-pointer text-foreground"
                >
                  <div className="flex items-center">
                    <span className="status-indicator status-completed mr-2"></span>
                    Laag
                  </div>
                </SelectItem>
                <SelectItem
                  value="medium"
                  className="hover:bg-accent focus:bg-accent cursor-pointer text-foreground"
                >
                  <div className="flex items-center">
                    <span className="status-indicator status-running mr-2"></span>
                    Gemiddeld
                  </div>
                </SelectItem>
                <SelectItem
                  value="high"
                  className="hover:bg-accent focus:bg-accent cursor-pointer text-foreground"
                >
                  <div className="flex items-center">
                    <span className="status-indicator status-error mr-2"></span>
                    Hoog
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-row gap-2 bg-card border border-border text-foreground focus:ring-primary rounded-xl pl-2 max-w-[100%] sm:max-w-[90%]">
            <div className="flex flex-row items-center text-sm ml-2 text-muted-foreground">
              <Cpu className="h-4 w-4 mr-2 text-cegeka-primary" />
              Model
            </div>
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger className="w-[150px] bg-transparent border-none cursor-pointer">
                <SelectValue placeholder="Model" />
              </SelectTrigger>
              <SelectContent className="bg-card border-border text-foreground cursor-pointer shadow-lg">
                <SelectItem
                  value="gemini-2.0-flash"
                  className="hover:bg-accent focus:bg-accent cursor-pointer text-foreground"
                >
                  <div className="flex items-center">
                    <Zap className="h-4 w-4 mr-2 text-cegeka-primary" /> 2.0 Flash
                  </div>
                </SelectItem>
                <SelectItem
                  value="gemini-2.5-flash-preview-04-17"
                  className="hover:bg-accent focus:bg-accent cursor-pointer text-foreground"
                >
                  <div className="flex items-center">
                    <Zap className="h-4 w-4 mr-2 text-cegeka-secondary" /> 2.5 Flash
                  </div>
                </SelectItem>
                <SelectItem
                  value="gemini-2.5-pro-preview-05-06"
                  className="hover:bg-accent focus:bg-accent cursor-pointer text-foreground"
                >
                  <div className="flex items-center">
                    <Cpu className="h-4 w-4 mr-2 text-cegeka-accent" /> 2.5 Pro
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        {hasHistory && (
          <Button
            className="btn-cegeka-secondary rounded-xl flex items-center gap-2"
            variant="default"
            onClick={() => window.location.reload()}
          >
            <SquarePen size={16} />
            Nieuwe Zoekopdracht
          </Button>
        )}
      </div>
    </form>
  );
};