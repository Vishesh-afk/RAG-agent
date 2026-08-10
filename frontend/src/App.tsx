import { Sidebar } from "./components/Sidebar";
import { ChatView } from "./components/ChatView";
import { useHealth } from "./hooks/useHealth";
import { useDocuments } from "./hooks/useDocuments";
import { useChat } from "./hooks/useChat";

function App() {
  const { online } = useHealth();
  const { documents, loading: documentsLoading, refresh, remove, removeAll } = useDocuments(online);
  const { messages, sending, send, reset } = useChat();

  return (
    <div className="flex h-screen w-full overflow-hidden bg-ink-900">
      <Sidebar
        online={online}
        documents={documents}
        documentsLoading={documentsLoading}
        onIngested={refresh}
        onDelete={remove}
        onDeleteAll={removeAll}
        onNewChat={reset}
      />
      <main className="flex min-w-0 flex-1 flex-col">
        {online === false && (
          <div className="border-b border-rust-500/30 bg-rust-500/[0.08] px-6 py-2 text-center text-xs text-rust-400">
            Backend API is offline — start it with{" "}
            <code className="rounded bg-ink-800 px-1 py-0.5 font-mono">uvicorn agent.api:app --port 8058</code>
          </div>
        )}
        <ChatView messages={messages} sending={sending} hasDocuments={documents.length > 0} onSend={send} />
      </main>
    </div>
  );
}

export default App;
