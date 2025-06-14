import { useState, useEffect, useRef, useCallback } from "react";
import { useADKStream, type Message } from "@/hooks/useADKStream";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ChatMessagesView } from "@/components/ChatMessagesView";
import cegekaLogo from "@/assets/images/cegeka-logo.png";

export default function App() {
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<
    ProcessedEvent[]
  >([]);
  const [historicalActivities, setHistoricalActivities] = useState<
    Record<string, ProcessedEvent[]>
  >({});
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const hasFinalizeEventOccurredRef = useRef(false);
  const seenFinalizeAnswer = useRef(false);

  const { messages, isLoading, startStream, stopStream } = useADKStream({
    onActivity: (event) => {
      let processedEvent: ProcessedEvent | null = null;
      
      // Map ADK events to processed events based on the event type
      const { event: eventType, data } = event;
      
      if (eventType === 'generate_query') {
        processedEvent = {
          title: "Zoekopdrachten Genereren",
          data: data.query_list ? data.query_list.join(", ") : "Opdrachten genereren...",
        };
      } else if (eventType === 'web_research') {
        const sources = data.sources_gathered || [];
        const numSources = sources.length;
        const uniqueLabels = [
          ...new Set(sources.map((s: any) => s.label).filter(Boolean)),
        ];
        const exampleLabels = uniqueLabels.slice(0, 3).join(", ");
        const iterationMsg = data.iteration && data.iteration > 1 ? ` (Iteration ${data.iteration})` : '';
        processedEvent = {
          title: `Web Onderzoek${iterationMsg}`,
          data: `${numSources} bronnen verzameld. Gerelateerd aan: ${
            exampleLabels || "N/A"
          }.`,
        };
      } else if (eventType === 'reflection') {
        const iterationMsg = data.iteration && data.iteration > 1 ? ` (Iteration ${data.iteration})` : '';
        processedEvent = {
          title: `Reflectie${iterationMsg}`,
          data: data.is_sufficient
            ? "Zoeken succesvol, eindantwoord genereren."
            : `Meer informatie nodig, zoeken naar ${
                data.follow_up_queries 
                  ? data.follow_up_queries.map((q: any) => typeof q === 'string' ? q : q.query).join(", ") 
                  : "aanvullende informatie"
              }`,
        };
      } else if (eventType === 'finalize_answer') {
        // Only add the first finalize_answer event
        if (!seenFinalizeAnswer.current) {
          seenFinalizeAnswer.current = true;
          processedEvent = {
            title: "Antwoord Afronden",
            data: "Eindantwoord samenstellen en presenteren.",
          };
          hasFinalizeEventOccurredRef.current = true;
        }
      }
      
      if (processedEvent) {
        setProcessedEventsTimeline((prevEvents) => [
          ...prevEvents,
          processedEvent!,
        ]);
      }
    },
    onComplete: () => {
      console.log("Stream completed");
    },
    onError: (error) => {
      console.error("Stream error:", error);
    }
  });

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [messages]);

  useEffect(() => {
    if (
      hasFinalizeEventOccurredRef.current &&
      !isLoading &&
      messages.length > 0
    ) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage && lastMessage.type === "ai" && lastMessage.id) {
        setHistoricalActivities((prev) => ({
          ...prev,
          [lastMessage.id!]: [...processedEventsTimeline],
        }));
      }
      hasFinalizeEventOccurredRef.current = false;
    }
  }, [messages, isLoading, processedEventsTimeline]);

  const handleSubmit = useCallback(
    (submittedInputValue: string, effort: string, model: string) => {
      if (!submittedInputValue.trim()) return;
      setProcessedEventsTimeline([]);
      hasFinalizeEventOccurredRef.current = false;
      seenFinalizeAnswer.current = false;  // Reset the flag for new questions

      // Start the ADK stream with the new format
      startStream({
        question: submittedInputValue,
        effort_level: effort as 'low' | 'medium' | 'high',
        reasoning_model: model,
      });
    },
    [startStream]
  );

  const handleCancel = useCallback(() => {
    stopStream();
    window.location.reload();
  }, [stopStream]);

  return (
    <div className="flex h-screen bg-background text-foreground font-sans antialiased">
      <main className="flex-1 flex flex-col overflow-hidden max-w-4xl mx-auto w-full">
        
        <div
          className={`flex-1 overflow-hidden ${
            messages.length === 0 ? "flex" : ""
          }`}
        >
          {messages.length === 0 ? (
            <WelcomeScreen
              handleSubmit={handleSubmit}
              isLoading={isLoading}
              onCancel={handleCancel}
            />
          ) : (
            <ChatMessagesView
              messages={messages}
              isLoading={isLoading}
              scrollAreaRef={scrollAreaRef}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              liveActivityEvents={processedEventsTimeline}
              historicalActivities={historicalActivities}
            />
          )}
        </div>
      </main>
    </div>
  );
}