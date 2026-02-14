import { useEffect, useState } from "react";
import { DataTable } from "@/components/DataTable";
import { ActionButtons } from "@/components/ActionButtons";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { TableCell, TableRow } from "@/components/table";
import { Badge } from "@/components/badge";
import { Button } from "@/components/button";
import { EmailAgentConfigResponse } from "@/interfaces/email-agent.interface";
import {
  getEmailAgentConfigs,
  triggerEmailAgent,
  deleteEmailAgentConfig,
} from "@/services/emailAgent";
import { toast } from "react-hot-toast";
import { Play, History } from "lucide-react";
import { EmailAgentHistoryDialog } from "./EmailAgentHistoryDialog";

interface Props {
  searchQuery: string;
  refreshKey?: number;
  onEdit: (item: EmailAgentConfigResponse) => void;
  onRefresh: () => void;
}

export function EmailAgentCard({
  searchQuery,
  refreshKey = 0,
  onEdit,
  onRefresh,
}: Props) {
  const [items, setItems] = useState<EmailAgentConfigResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [itemToDelete, setItemToDelete] =
    useState<EmailAgentConfigResponse | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [triggeringId, setTriggeringId] = useState<string | null>(null);
  const [historyDsId, setHistoryDsId] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, [refreshKey]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await getEmailAgentConfigs();
      setItems(data);
    } catch {
      toast.error("Failed to fetch email agent configurations.");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!itemToDelete) return;
    setIsDeleting(true);
    try {
      await deleteEmailAgentConfig(itemToDelete.data_source_id);
      toast.success("Email agent configuration removed.");
      onRefresh();
    } catch {
      toast.error("Failed to remove email agent configuration.");
    } finally {
      setIsDeleting(false);
      setIsDeleteDialogOpen(false);
    }
  };

  const handleTrigger = async (dsId: string) => {
    setTriggeringId(dsId);
    try {
      await triggerEmailAgent(dsId);
      toast.success("Email agent processing triggered.");
    } catch {
      toast.error("Failed to trigger email agent.");
    } finally {
      setTriggeringId(null);
    }
  };

  const filtered = items.filter((item) =>
    item.data_source_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const headers = [
    "Data Source",
    "Mode",
    "Polling",
    "Max Emails",
    "Actions",
  ];

  const renderRow = (item: EmailAgentConfigResponse) => {
    const config = item.email_agent_config;
    const isConfigured = item.has_email_agent;

    return (
      <TableRow key={item.data_source_id}>
        <TableCell className="font-medium">{item.data_source_name}</TableCell>
        <TableCell>
          {isConfigured ? (
            <Badge
              variant={
                config?.mode === "autonomous" ? "default" : "secondary"
              }
            >
              {config?.mode === "autonomous" ? "Autonomous" : "Recommend Only"}
            </Badge>
          ) : (
            <span className="text-muted-foreground text-sm">
              Not configured
            </span>
          )}
        </TableCell>
        <TableCell>
          {isConfigured ? (
            <Badge variant={config?.polling_enabled ? "default" : "outline"}>
              {config?.polling_enabled ? "On" : "Off"}
            </Badge>
          ) : (
            <span className="text-muted-foreground text-sm">-</span>
          )}
        </TableCell>
        <TableCell>
          {isConfigured ? config?.max_emails_per_poll ?? 10 : "-"}
        </TableCell>
        <TableCell>
          <div className="flex items-center gap-1">
            {isConfigured && (
              <>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => handleTrigger(item.data_source_id)}
                  disabled={triggeringId === item.data_source_id}
                  title="Run Now"
                >
                  <Play className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setHistoryDsId(item.data_source_id)}
                  title="View History"
                >
                  <History className="h-4 w-4" />
                </Button>
              </>
            )}
            <ActionButtons
              onEdit={() => onEdit(item)}
              onDelete={
                isConfigured
                  ? () => {
                      setItemToDelete(item);
                      setIsDeleteDialogOpen(true);
                    }
                  : undefined
              }
              editTitle="Configure Email Agent"
              deleteTitle="Remove Configuration"
            />
          </div>
        </TableCell>
      </TableRow>
    );
  };

  return (
    <>
      <DataTable
        data={filtered}
        loading={loading}
        error={null}
        searchQuery={searchQuery}
        headers={headers}
        renderRow={renderRow}
        emptyMessage="No Gmail data sources found. Add a Gmail data source first."
        searchEmptyMessage="No matching data sources"
      />

      <ConfirmDialog
        isOpen={isDeleteDialogOpen}
        onOpenChange={setIsDeleteDialogOpen}
        onConfirm={handleDelete}
        isInProgress={isDeleting}
        itemName={itemToDelete?.data_source_name || ""}
        description={`This will remove the email agent configuration from "${itemToDelete?.data_source_name}". The data source itself will not be deleted.`}
      />

      {historyDsId && (
        <EmailAgentHistoryDialog
          dsId={historyDsId}
          isOpen={!!historyDsId}
          onOpenChange={(open) => {
            if (!open) setHistoryDsId(null);
          }}
        />
      )}
    </>
  );
}
