import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Loader2,
  Activity,
  Info,
  Search,
  TextSearch,
  Brain,
  Pen,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useEffect, useState } from "react";

export interface ProcessedEvent {
  title: string;
  data: any;
}

interface ActivityTimelineProps {
  processedEvents: ProcessedEvent[];
  isLoading: boolean;
}

export function ActivityTimeline({
  processedEvents,
  isLoading,
}: ActivityTimelineProps) {
  const [isTimelineCollapsed, setIsTimelineCollapsed] =
    useState<boolean>(false);
  const getEventIcon = (title: string, index: number) => {
    if (index === 0 && isLoading && processedEvents.length === 0) {
      return <Loader2 className="h-4 w-4 text-cegeka-primary animate-spin" />;
    }
    if (title.toLowerCase().includes("generating")) {
      return <TextSearch className="h-4 w-4 text-cegeka-primary" />;
    } else if (title.toLowerCase().includes("thinking")) {
      return <Loader2 className="h-4 w-4 text-cegeka-primary animate-spin" />;
    } else if (title.toLowerCase().includes("reflection")) {
      return <Brain className="h-4 w-4 text-cegeka-accent" />;
    } else if (title.toLowerCase().includes("research")) {
      return <Search className="h-4 w-4 text-cegeka-secondary" />;
    } else if (title.toLowerCase().includes("finalizing")) {
      return <Pen className="h-4 w-4 text-cegeka-primary" />;
    }
    return <Activity className="h-4 w-4 text-muted-foreground" />;
  };

  useEffect(() => {
    if (!isLoading && processedEvents.length !== 0) {
      setIsTimelineCollapsed(true);
    }
  }, [isLoading, processedEvents]);

  return (
    <Card className="card-cegeka max-h-96">
      <CardHeader className="pb-3">
        <CardDescription className="flex items-center justify-between">
          <div
            className="flex items-center justify-start text-sm w-full cursor-pointer gap-2 text-foreground font-semibold"
            onClick={() => setIsTimelineCollapsed(!isTimelineCollapsed)}
          >
            <span className="status-indicator status-running"></span>
            Research Progress
            {isTimelineCollapsed ? (
              <ChevronDown className="h-4 w-4 mr-2 text-cegeka-primary" />
            ) : (
              <ChevronUp className="h-4 w-4 mr-2 text-cegeka-primary" />
            )}
          </div>
        </CardDescription>
      </CardHeader>
      {!isTimelineCollapsed && (
        <ScrollArea className="max-h-96 overflow-y-auto">
          <CardContent>
            {isLoading && processedEvents.length === 0 && (
              <div className="timeline-item active animate-pulse-cegeka">
                <div>
                  <p className="text-sm text-foreground font-medium flex items-center gap-2">
                    <span className="status-indicator status-running"></span>
                    Initializing research...
                  </p>
                </div>
              </div>
            )}
            {processedEvents.length > 0 ? (
              <div className="space-y-0">
                {processedEvents.map((eventItem, index) => (
                  <div 
                    key={index} 
                    className={`timeline-item ${
                      index === processedEvents.length - 1 && isLoading 
                        ? 'active' 
                        : 'completed'
                    } animate-fadeInUp`}
                    style={{ animationDelay: `${index * 0.1}s` }}
                  >
                    <div>
                      <p className="text-sm text-foreground font-medium mb-1 flex items-center gap-2">
                        {getEventIcon(eventItem.title, index)}
                        {eventItem.title}
                      </p>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        {typeof eventItem.data === "string"
                          ? eventItem.data
                          : Array.isArray(eventItem.data)
                          ? (eventItem.data as string[]).join(", ")
                          : JSON.stringify(eventItem.data)}
                      </p>
                    </div>
                  </div>
                ))}
                {isLoading && processedEvents.length > 0 && (
                  <div className="timeline-item active animate-pulse-cegeka">
                    <div>
                      <p className="text-sm text-foreground font-medium flex items-center gap-2">
                        <span className="status-indicator status-running"></span>
                        Processing...
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ) : !isLoading ? ( // Only show "No activity" if not loading and no events
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground pt-10">
                <Info className="h-6 w-6 mb-3 text-cegeka-primary" />
                <p className="text-sm">No activity to display.</p>
                <p className="text-xs text-muted-foreground/70 mt-1">
                  Timeline will update during processing.
                </p>
              </div>
            ) : null}
          </CardContent>
        </ScrollArea>
      )}
    </Card>
  );
}