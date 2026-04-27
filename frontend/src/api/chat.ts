/*
 * File: chat.ts
 * Name: Keagan Weinstock
*/

import axios from "axios";

const API_URL = "http://100.82.231.125:8000";

export type Message = {
  role: "user" | "assistant";
  content: string;
};

export type Conversation = {
    id: string;
    title: string;
    messages: Message[];
}

export type ToolEvent = {
    name: string;
    args: Record<string, unknown>
}

export async function sendMessage(
    messages: Message[],
    onToken: (token: string) => void,
    onTool?: (tool: ToolEvent) => void
): Promise<void> {
    const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages }),
    });

    const reader = res.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        for (const line of text.split("\n")) {
            if (!line.startsWith("data: ")) continue;
            const data = line.slice(6);
            if (data === "[DONE]") return;
            try {
                const parsed = JSON.parse(data);
                if (parsed.error) {
                    onToken(`\n\nError: ${parsed.error}`);
                    return;
                }
                if (parsed.token) onToken(parsed.token);
                if (parsed.tool) onTool?.({name: parsed.tool, args: parsed.args})
            } catch {
                // malformed chunk, skip
            }
        }
    }
}

export async function loadHistory() {
    const res = await axios.get(`${API_URL}/history`);
    return res.data;
}

export async function saveHistory(conversations: Conversation[]) {
    await axios.post(`${API_URL}/history`, { conversations });
}

export async function uploadFile(file: File): Promise<string> {
    const form = new FormData();
    form.append("file", file);
    const res = await axios.post(`${API_URL}/upload`, form);
    return res.data.filename;
}

export async function getUploadedFiles(): Promise<string[]> {
    const res = await axios.get(`${API_URL}/uploads`);
    return res.data;
}

export async function deleteFile(filename: string): Promise<void> {
    await axios.delete(`${API_URL}/uploads/${filename}`)
}

export async function getStats(): Promise<{
    ram_used_gb: number;
    ram_total_gb: number;
    tier: string;
    n_ctx: number;
}> {
    const res = await axios.get(`${API_URL}/stats`);
    return res.data;
}