import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/dialog";
import { Badge } from "@/components/badge";
import { EmailAgentHistory } from "@/interfaces/email-agent.interface";
import { getEmailAgentHistory } from "@/services/emailAgent";
import { toast } from "react-hot-toast";
import { formatDate } from "@/helpers/utils";

interface Props {
  dsId: string;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

const ACTION_LABELS: Record<string, string> = {
  reply_to_email: "Replied",
  mark_as_read: "Marked Read",
  forward_email: "Forwarded",
  flag_for_review: "Flagged",
  categorize: "Categorized",
  ignore: "Ignored",
  recommendation: "Recommendation",
  no_action: "No Action",
};

const ACTION_VARIANTS: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
  reply_to_email: "default",
  mark_as_read: "secondary",
  forward_email: "default",
  flag_for_review: "destructive",
  categorize: "outline",
  ignore: "secondary",
  recommendation: "outline",
  no_action: "secondary",
};

export function EmailAgentHistoryDialog({ dsId, isOpen, onOpenChange }: Props) {
  const [history, setHistory] = useState<EmailAgentHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOpen && dsId) {
      fetchHistory();
    }
  }, [isOpen, dsId]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await getEmailAgentHistory(dsId);
      setHistory(data.history);
    } catch {
      toast.error("Failed to load processing history.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px] p-0 overflow-hidden">
        <DialogHeader className="p-6 pb-4">
          <DialogTitle>Email Agent History</DialogTitle>
        </DialogHeader>

        <div className="px-6 pb-6 max-h-[70vh] overflow-y-auto">
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading history...
            </div>
          ) : history.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No processing history yet. Trigger the email agent to start
              processing emails.
            </div>
          ) : (
            <div className="space-y-3">
              {history.map((entry, index) => (
                <div
                  key={`${entry.email_id}-${index}`}
                  className="border rounded-lg p-3 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          ACTION_VARIANTS[entry.action_taken] || "secondary"
                        }
                      >
                        {ACTION_LABELS[entry.action_taken] ||
                          entry.action_taken}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {entry.mode === "autonomous"
                          ? "Auto"
                          : "Recommend"}
                      </Badge>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {formatDate(entry.timestamp)}
                    </span>
                  </div>
                  <div className="text-sm">
                    <span className="text-muted-foreground">From:</span>{" "}
                    {entry.from}
                  </div>
                  <div className="text-sm font-medium">{entry.subject}</div>
                  {entry.agent_reasoning && (
                    <details className="text-xs text-muted-foreground">
                      <summary className="cursor-pointer hover:text-foreground">
                        Agent Reasoning
                      </summary>
                      <pre className="mt-1 whitespace-pre-wrap bg-muted p-2 rounded text-xs max-h-40 overflow-y-auto">
                        {entry.agent_reasoning}
                      </pre>
                    </details>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
