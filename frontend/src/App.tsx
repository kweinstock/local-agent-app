/* File: APP.tsx
 * Name: Keagan Weinstock
*/

import { useState, useEffect, useRef } from "react";
import {
    type Conversation,
    loadHistory,
    type Message,
    saveHistory,
    sendMessage,
    uploadFile,
    getUploadedFiles,
    getStats,
    deleteFile,
} from "./api/chat.ts";

import MessageBubble from "./components/MessageBubble.tsx";
import "./App.css";
import * as React from "react";

export default function App() {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [activeId, setActiveId] = useState<string | null>(null);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
    const [showFiles, setShowFiles] = useState(false);
    const [stats, setStats] = useState<{
        ram_used_gb: number;
        ram_total_gb: number;
        tier: string;
        n_ctx: number;
    } | null>(null);

    const chatEndRef = useRef<HTMLDivElement>(null);

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const filename = await uploadFile(file);
        setUploadedFiles(prev => [...prev, filename]);
    };

    const handleDeleteFile = async (filename: string) => {
        await deleteFile(filename);
        setUploadedFiles(prev => prev.filter(f => f !== filename))
    }

    const createConversation = (): Conversation => ({
        id: crypto.randomUUID(),
        title: "New Chat",
        messages: [],
    });

    const activeConversation = conversations.find(c => c.id === activeId) ?? null;
    const lastMsg = activeConversation?.messages.at(-1)
    const isStreaming = loading && lastMsg?.role === "assistant" && lastMsg?.content === "";

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
        const id = setInterval(poll, 5000);
        return () => clearInterval(id);
    }, []);

    useEffect(() => {
        if (conversations.length > 0) saveHistory(conversations);
    }, [conversations]);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [conversations, activeId]);

    const newChat = () => {
        const conv = createConversation();
        setConversations(prev => [conv, ...prev]);
        setActiveId(conv.id);
    };

    const switchChat = (id: string) => setActiveId(id);

    const deleteConversation = (id: string) => {
        setConversations(prev => {
            const updated = prev.filter(c => c.id !== id);
            if (activeId === id) setActiveId(updated[0]?.id ?? null);
            return updated;
        });
    };

    const handleSend = async () => {
        if (!input.trim() || !activeConversation) return;

        const userMessage: Message = { role: "user", content: input };
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

        let streamed = "";

        const streamingConversation: Conversation = {
            ...updatedConversation,
            messages: [...updatedConversation.messages, { role: "assistant", content: "" }],
        };
        setConversations(prev =>
            prev.map(c => c.id === activeConversation.id ? streamingConversation : c)
        );

        try {
            await sendMessage(updatedConversation.messages, (token) => {
                streamed += token;
                setConversations(prev => prev.map(c => {
                    if (c.id !== activeConversation.id) return c;
                    const msgs = [...c.messages];
                    msgs[msgs.length - 1] = { role: "assistant", content: streamed };
                    return { ...c, messages: msgs };
                }));
            });
        } catch (err) {
            console.error("Stream error:", err);
            setConversations(prev => prev.map(c => {
                if (c.id !== activeConversation.id) return c;
                const msgs = [...c.messages];
                msgs[msgs.length - 1] = { role: "assistant", content: "Error connecting to backend." };
                return { ...c, messages: msgs };
            }));
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
                        <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>{c.title}</span>
                        <button className="deleteBtn" onClick={(e) => {
                            e.stopPropagation();
                            deleteConversation(c.id);
                        }}>✕</button>
                    </div>
                ))}
                {stats && (
                    <div className="statsPanel">
                        <div className="statRow">
                            <span className="statLabel">RAM</span>
                            <span className="statValue">{stats.ram_used_gb} / {stats.ram_total_gb} GB</span>
                        </div>
                        <div className="statRow">
                            <span className="statLabel">Tier</span>
                            <span className="statValue" style={{
                                color: stats.tier === "high" ? "#3c3cff"
                                     : stats.tier === "medium" ? "#cc8833"
                                     : "#cc3333"
                            }}>{stats.tier}</span>
                        </div>
                        <div className="statRow">
                            <span className="statLabel">CTX</span>
                            <span className="statValue">{stats.n_ctx.toLocaleString()}</span>
                        </div>
                    </div>
                )}
            </div>

            {/* MAIN CHAT AREA */}
            <div className="container">
                <div className="chat">
                    {activeConversation?.messages
                        .filter(m => m.content !== "")
                        .map((m, i) => (
                        <MessageBubble key={i} role={m.role} content={m.content} />
                    ))}
                    {isStreaming && (
                        <div className="thinking">
                            <span /><span /><span />
                        </div>
                    )}
                    <div ref={chatEndRef} />
                </div>

                {showFiles && uploadedFiles.length > 0 && (
                    <div className="filesPanel">
                        <div className="filesPanelHeader">Uploaded Files</div>
                        {uploadedFiles.map(f => (
                            <div key={f} className="fileRow">
                                <span className="fileIcon">📄</span>
                                <span className="fileName">{f}</span>
                                <button className="deleteBtn" onClick={() => handleDeleteFile(f)}>✕</button>
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

                    <textarea
                        className="chatInput"
                        value={input}
                        onChange={(e) => {
                            setInput(e.target.value);
                            e.target.style.height = "auto";
                            e.target.style.height = `${e.target.scrollHeight}px`;
                        }}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault();
                                handleSend();
                            }
                        }}
                        placeholder="Ask something... (Shift+Enter for new line)"
                        rows={1}
                    />
                    <button onClick={handleSend}>Send</button>
                </div>
            </div>
        </div>
    );
}