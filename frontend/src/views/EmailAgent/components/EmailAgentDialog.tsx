import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/select";
import { Input } from "@/components/input";
import { Label } from "@/components/label";
import { Textarea } from "@/components/textarea";
import { Switch } from "@/components/switch";
import { Separator } from "@/components/separator";
import { Button } from "@/components/button";
import { Checkbox } from "@/components/checkbox";
import { toast } from "react-hot-toast";
import {
  EmailAgentConfigResponse,
  EmailAgentMode,
  AVAILABLE_ACTIONS,
  DEFAULT_ALLOWED_ACTIONS,
} from "@/interfaces/email-agent.interface";
import { updateEmailAgentConfig } from "@/services/emailAgent";
import { getAllLLMProviders } from "@/services/llmProviders";
import { LLMProvider } from "@/interfaces/llmProvider.interface";

interface Props {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved?: () => void;
  mode?: "create" | "edit";
  itemToEdit?: EmailAgentConfigResponse | null;
}

export function EmailAgentDialog({
  isOpen,
  onOpenChange,
  onSaved,
  mode = "create",
  itemToEdit,
}: Props) {
  const [pollingEnabled, setPollingEnabled] = useState(true);
  const [agentMode, setAgentMode] = useState<EmailAgentMode>("autonomous");
  const [llmProviderId, setLlmProviderId] = useState<string>("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [rules, setRules] = useState("");
  const [maxEmailsPerPoll, setMaxEmailsPerPoll] = useState(10);
  const [autoMarkAsRead, setAutoMarkAsRead] = useState(true);
  const [allowedActions, setAllowedActions] = useState<string[]>(
    DEFAULT_ALLOWED_ACTIONS
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [llmProviders, setLlmProviders] = useState<LLMProvider[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(false);

  useEffect(() => {
    if (isOpen) {
      const fetchData = async () => {
        setIsLoadingData(true);
        try {
          const providers = await getAllLLMProviders();
          setLlmProviders(providers);
        } catch {
          toast.error("Failed to load LLM providers");
        } finally {
          setIsLoadingData(false);
        }
      };

      fetchData();

      if (mode === "edit" && itemToEdit?.email_agent_config) {
        const config = itemToEdit.email_agent_config;
        setPollingEnabled(config.polling_enabled);
        setAgentMode(config.mode);
        setLlmProviderId(config.llm_provider_id || "");
        setSystemPrompt(config.system_prompt || "");
        setRules(config.rules || "");
        setMaxEmailsPerPoll(config.max_emails_per_poll);
        setAutoMarkAsRead(config.auto_mark_as_read);
        setAllowedActions(config.allowed_actions || DEFAULT_ALLOWED_ACTIONS);
      } else {
        setPollingEnabled(true);
        setAgentMode("autonomous");
        setLlmProviderId("");
        setSystemPrompt("");
        setRules("");
        setMaxEmailsPerPoll(10);
        setAutoMarkAsRead(true);
        setAllowedActions(DEFAULT_ALLOWED_ACTIONS);
      }
    }
  }, [isOpen, mode, itemToEdit]);

  const toggleAction = (action: string) => {
    setAllowedActions((prev) =>
      prev.includes(action)
        ? prev.filter((a) => a !== action)
        : [...prev, action]
    );
  };

  const handleSubmit = async () => {
    if (!itemToEdit) {
      toast.error("Please select a data source first.");
      return;
    }

    setIsSubmitting(true);
    try {
      await updateEmailAgentConfig(itemToEdit.data_source_id, {
        polling_enabled: pollingEnabled,
        mode: agentMode,
        llm_provider_id: llmProviderId || null,
        system_prompt: systemPrompt || null,
        rules: rules || null,
        max_emails_per_poll: maxEmailsPerPoll,
        auto_mark_as_read: autoMarkAsRead,
        allowed_actions: allowedActions,
      });

      toast.success("Email agent configuration saved.");
      onSaved?.();
      onOpenChange(false);
    } catch {
      toast.error("Failed to save email agent configuration.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[550px] p-0 overflow-hidden">
        <DialogHeader className="p-6 pb-4">
          <DialogTitle>
            {mode === "create"
              ? "Configure Email Agent"
              : `Edit Email Agent - ${itemToEdit?.data_source_name || ""}`}
          </DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 px-6 pb-6 max-h-[70vh] overflow-y-auto overflow-x-hidden">
          {/* Data Source Info */}
          {itemToEdit && (
            <div>
              <Label>Gmail Data Source</Label>
              <Input
                value={itemToEdit.data_source_name}
                readOnly
                className="bg-gray-100 cursor-not-allowed"
              />
            </div>
          )}

          <Separator className="my-1" />

          {/* Agent Mode */}
          <div>
            <Label htmlFor="agent-mode">Agent Mode</Label>
            <Select
              value={agentMode}
              onValueChange={(value) => setAgentMode(value as EmailAgentMode)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select agent mode" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="autonomous">
                  Autonomous - Agent acts on emails automatically
                </SelectItem>
                <SelectItem value="recommend_only">
                  Recommend Only - Agent suggests actions for human approval
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* LLM Provider */}
          <div>
            <Label htmlFor="llm-provider">LLM Provider</Label>
            <Select
              value={llmProviderId || "default"}
              onValueChange={(value) =>
                setLlmProviderId(value === "default" ? "" : value)
              }
              disabled={isLoadingData}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select LLM provider" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="default">Default Provider</SelectItem>
                {llmProviders.map((provider) => (
                  <SelectItem key={provider.id} value={provider.id}>
                    {provider.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Separator className="my-1" />

          {/* Polling */}
          <div className="flex items-center space-x-2">
            <Switch
              id="polling-enabled"
              checked={pollingEnabled}
              onCheckedChange={setPollingEnabled}
            />
            <Label htmlFor="polling-enabled">Enable Polling</Label>
          </div>

          {/* Max Emails */}
          <div>
            <Label htmlFor="max-emails">Max Emails Per Poll</Label>
            <Input
              id="max-emails"
              type="number"
              min={1}
              max={50}
              value={maxEmailsPerPoll}
              onChange={(e) =>
                setMaxEmailsPerPoll(
                  Math.min(50, Math.max(1, parseInt(e.target.value) || 10))
                )
              }
            />
          </div>

          {/* Auto Mark as Read */}
          <div className="flex items-center space-x-2">
            <Switch
              id="auto-mark-read"
              checked={autoMarkAsRead}
              onCheckedChange={setAutoMarkAsRead}
            />
            <Label htmlFor="auto-mark-read">
              Auto Mark as Read (autonomous mode)
            </Label>
          </div>

          <Separator className="my-1" />

          {/* Allowed Actions */}
          {agentMode === "autonomous" && (
            <div>
              <Label className="mb-2 block">Allowed Actions</Label>
              <div className="grid grid-cols-2 gap-2">
                {AVAILABLE_ACTIONS.map((action) => (
                  <div
                    key={action.value}
                    className="flex items-center space-x-2"
                  >
                    <Checkbox
                      id={`action-${action.value}`}
                      checked={allowedActions.includes(action.value)}
                      onCheckedChange={() => toggleAction(action.value)}
                    />
                    <Label
                      htmlFor={`action-${action.value}`}
                      className="text-sm font-normal"
                    >
                      {action.label}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
          )}

          <Separator className="my-1" />

          {/* Custom Rules */}
          <div>
            <Label htmlFor="rules">Custom Rules</Label>
            <Textarea
              id="rules"
              value={rules}
              onChange={(e) => setRules(e.target.value)}
              rows={3}
              placeholder="e.g., Always flag emails from legal@company.com for review. Forward support emails to team@company.com."
            />
          </div>

          {/* Custom System Prompt */}
          <div>
            <Label htmlFor="system-prompt">
              Custom System Prompt (Advanced)
            </Label>
            <Textarea
              id="system-prompt"
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={4}
              placeholder="Leave empty to use the default prompt. Only override if you need full control over the agent's behavior."
            />
          </div>
        </div>

        <DialogFooter className="px-6 py-4 border-t">
          <div className="flex justify-end gap-3 w-full">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Save Configuration"}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
