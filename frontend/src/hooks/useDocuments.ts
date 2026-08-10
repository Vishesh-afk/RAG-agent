import { useCallback, useEffect, useState } from "react";
import { deleteAllDocuments, deleteDocument, listDocuments } from "../lib/api";
import type { DocumentMetadata } from "../lib/types";

export function useDocuments(online: boolean | null) {
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch {
      // leave the last known list in place rather than clearing it on a blip
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (online) refresh();
  }, [online, refresh]);

  const remove = useCallback(
    async (id: string) => {
      setDocuments((prev) => prev.filter((d) => d.id !== id));
      try {
        await deleteDocument(id);
      } finally {
        refresh();
      }
    },
    [refresh]
  );

  const removeAll = useCallback(async () => {
    setDocuments([]);
    try {
      await deleteAllDocuments();
    } finally {
      refresh();
    }
  }, [refresh]);

  return { documents, loading, refresh, remove, removeAll };
}
