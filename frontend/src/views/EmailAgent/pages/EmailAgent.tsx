import { useState } from "react";
import { PageLayout } from "@/components/PageLayout";
import { PageHeader } from "@/components/PageHeader";
import { EmailAgentConfigResponse } from "@/interfaces/email-agent.interface";
import { EmailAgentCard } from "../components/EmailAgentCard";
import { EmailAgentDialog } from "../components/EmailAgentDialog";

export default function EmailAgentPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [dialogMode, setDialogMode] = useState<"create" | "edit">("create");
  const [itemToEdit, setItemToEdit] = useState<EmailAgentConfigResponse | null>(
    null
  );

  const handleSaved = () => {
    setRefreshKey((prev) => prev + 1);
  };

  const handleConfigure = () => {
    setDialogMode("create");
    setItemToEdit(null);
    setIsDialogOpen(true);
  };

  const handleEdit = (item: EmailAgentConfigResponse) => {
    setDialogMode("edit");
    setItemToEdit(item);
    setIsDialogOpen(true);
  };

  return (
    <PageLayout>
      <PageHeader
        title="Email Agent"
        subtitle="Configure AI agents to monitor and act on incoming emails"
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search data sources..."
        actionButtonText="Configure Email Agent"
        onActionClick={handleConfigure}
      />

      <EmailAgentCard
        searchQuery={searchQuery}
        refreshKey={refreshKey}
        onEdit={handleEdit}
        onRefresh={handleSaved}
      />

      <EmailAgentDialog
        isOpen={isDialogOpen}
        onOpenChange={setIsDialogOpen}
        onSaved={handleSaved}
        itemToEdit={itemToEdit}
        mode={dialogMode}
      />
    </PageLayout>
  );
}
