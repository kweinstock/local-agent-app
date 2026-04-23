/* File: APP.tsx
 * Name: Keagan Weinstock
*/

import { useState, useEffect } from "react"
import {
    type Conversation,
    loadHistory,
    type Message,
    saveHistory,
    sendMessage,
    uploadFile,
    getUploadedFiles,
    getStats
} from "./api/chat.ts";

import MessageBubble from "./components/MessageBubble.tsx";
import "./App.css"
import * as React from "react";

export default function App() {
    const [conversations, setConversations] = useState<Conversation[]>([])
    const [activeId, setActiveId] = useState<string | null>(null);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
    const [showFiles, setShowFiles] = useState(false);
    const [stats, setStats] = useState<{
        ram_used_gb: number;
        ram_total_gb: number;
    } | null>(null);

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const filename = await uploadFile(file);
        setUploadedFiles(prev => [...prev, filename])
    }

    const createConversation = (): Conversation => ({
        id: crypto.randomUUID(),
        title: "New Chat",
        messages: [],
    });

    const activeConversation = conversations.find(c => c.id === activeId) ?? null;

    useEffect(() => {
        loadHistory().then((saved) => {
            if (saved.length > 0) {
                setConversations(saved);
                setActiveId(saved[0].id);
            } else {
                const first = createConversation();
                setConversations([first]);
                setActiveId(first.id);
            }
        });
        getUploadedFiles().then(setUploadedFiles);
    }, []);

    useEffect(() => {
        const poll = async () => setStats(await getStats());
        poll();
        const id = setInterval(poll, 5000)
        return () => clearInterval(id);
    }, []);

    useEffect(() => {
        if (conversations.length > 0) {
            saveHistory(conversations);
        }
    }, [conversations])

    const newChat = () => {
        const conv = createConversation();
        setConversations(prev => [conv, ...prev]);
        setActiveId(conv.id);
    };

    const switchChat = (id: string) => {
        setActiveId(id);
    }

    const handleSend = async () => {
        if (!input.trim() || !activeConversation) return;

        const userMessage: Message = {
            role: "user",
            content: input,
        };

        const updatedConversation: Conversation = {
            ...activeConversation,
            title: activeConversation.messages.length === 0
                ? input.slice(0, 28) + (input.length > 28 ? "..." : "")
                : activeConversation.title,
            messages: [...activeConversation.messages, userMessage],
        };

        setConversations(prev =>
            prev.map(c => c.id === activeConversation.id ? updatedConversation : c)
        );

        setInput("");
        setLoading(true);

        try {
            const response = await sendMessage(updatedConversation.messages);

            const assistantMessage: Message = {
                role: "assistant",
                content: response,
            };

            const finalConversation: Conversation = {
                ...updatedConversation,
                messages: [...updatedConversation.messages, assistantMessage],
            };

            setConversations(prev =>
                prev.map(c => (c.id === activeConversation.id ? finalConversation : c))
            );

        } catch (err) {
             const errorMessage: Message = {
                    role: "assistant",
                    content: "Error connecting to backend.",
             };
             const failedConversation = {
                 ...updatedConversation,
                 messages: [...updatedConversation.messages, errorMessage],
             };
             setConversations(prev =>
                 prev.map(c =>
                     c.id === activeConversation.id ? failedConversation : c
                 )
             );

        } finally {
            setLoading(false);
        }
    };

    return (
  <div className="appLayout">

    {/* SIDEBAR */}
    <div className="sidebar">
      <button className="newChatBtn" onClick={newChat}>+ New Chat</button>
        {conversations.map((c) => (
            <div
                key={c.id}
                className={`chatItem ${c.id === activeId ? "active" : ""}`}
                onClick={() => switchChat(c.id)}
            >
                {c.title}
            </div>
      ))}
        {stats && (
            <div className="statsPanel">
                <div className="statRow">
                    <span className="statLabel">RAM</span>
                    <span className="statValue">{stats.ram_used_gb} / {stats.ram_total_gb} GB</span>
                </div>
            </div>
        )}
    </div>

    {/* MAIN CHAT AREA */}
    <div className="container">

      <div className="chat">
        {activeConversation?.messages.map((m, i) => (
            <MessageBubble key={i} role={m.role} content={m.content} />
        ))}

        {loading && (
            <div className="thinking">
                <span /><span /><span />
            </div>
        )}
      </div>
        {showFiles && uploadedFiles.length > 0 && (
            <div className="filesPanel">
                <div className="filesPanelHeader">Uploaded Files</div>
                {uploadedFiles.map(f => (
                    <div key={f} className="fileRow">
                        <span className="fileIcon">📄</span>
                        <span className="fileName">{f}</span>
                    </div>
                ))}
            </div>
        )}
      <div className="inputBar">
        <label className="uploadBtn" title="Upload file">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 1v9M4 4l4-3 4 3M2 12h12v2H2z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <input type="file" hidden onChange={handleUpload} />
        </label>

        {uploadedFiles.length > 0 && (
            <button className="filesBtn" onClick={() => setShowFiles(p => !p)}>
                {uploadedFiles.length} file{uploadedFiles.length > 1 ? "s" : ""}
            </button>
        )}

        <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask Something..."
        />
        <button onClick={handleSend}>Send</button>
    </div>

    </div>
  </div>
);
}