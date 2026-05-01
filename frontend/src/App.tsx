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
    type WorkspaceFile,
    getWorkspaceFiles,
    deleteWorkspaceFile,
    getWorkspaceDownloadUrl,
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
    const [workspaceFiles, setWorkspaceFiles] = useState<WorkspaceFile[]>([]);
    const [showFiles, setShowFiles] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [workspaceExpanded, setWorkspaceExpanded] = useState(true);
    const [chatsExpanded, setChatsExpanded] = useState(true);
    const [toolStatus, setToolStatus] = useState<string | null>(null);
    const [stats, setStats] = useState<{
        ram_used_gb: number;
        ram_total_gb: number;
        tier: string;
        n_ctx: number;
    } | null>(null);

    const chatEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const filename = await uploadFile(file);
        setUploadedFiles(prev => [...prev, filename]);
    };

    const handleDeleteFile = async (filename: string) => {
        await deleteFile(filename);
        setUploadedFiles(prev => prev.filter(f => f !== filename));
    };

    const createConversation = (): Conversation => ({
        id: crypto.randomUUID(),
        title: "New Chat",
        messages: [],
    });

    const activeConversation = conversations.find(c => c.id === activeId) ?? null;
    const lastMsg = activeConversation?.messages.at(-1);
    const isStreaming = loading && lastMsg?.role === "assistant" && lastMsg?.content === "";
    const showTool = toolStatus && loading;
    const showThinking = isStreaming && !toolStatus;

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
        const poll = async () => {
            setStats(await getStats());
            setWorkspaceFiles(await getWorkspaceFiles());
        };
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
        if (textareaRef.current) textareaRef.current.style.height = "auto";
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
                setToolStatus(null);
                setConversations(prev => prev.map(c => {
                    if (c.id !== activeConversation.id) return c;
                    const msgs = [...c.messages];
                    msgs[msgs.length - 1] = { role: "assistant", content: streamed };
                    return { ...c, messages: msgs };
                }));
            }, (tool) => {
                const icons: Record<string, string> = {
                    run_python: "Running Python...",
                    read_file: "Reading file...",
                    search_context: "Searching files...",
                    search_files: "Searching for symbol...",
                    write_file: "Writing file...",
                    list_files: "Listing files...",
                };
                setToolStatus(icons[tool.name] ?? `Using ${tool.name}...`);
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
            setToolStatus(null);
        }
    };

    const totalFiles = uploadedFiles.length;

    return (
        <div className="appLayout">

            {/* SIDEBAR */}
            <div className={`sidebar ${sidebarOpen ? "" : "collapsed"}`}>

                <div className="sidebarTop">
                    <button className="newChatBtn" onClick={newChat}>
                        <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
                            <path d="M8 2v12M2 8h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                        </svg>
                        New chat
                    </button>
                    <button className="collapseBtn" onClick={() => setSidebarOpen(false)} title="Close sidebar">
                        <svg width="11" height="11" viewBox="0 0 16 16" fill="none">
                            <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                    </button>
                </div>

                {/* WORKSPACE SECTION */}
                {workspaceFiles.length > 0 && (
                    <>
                        <div className="sectionHeader" onClick={() => setWorkspaceExpanded(p => !p)}>
                            <span className="sectionLabel">Workspace</span>
                            <svg className={`sectionToggle ${workspaceExpanded ? "open" : ""}`} width="10" height="10" viewBox="0 0 16 16" fill="none">
                                <path d="M6 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg>
                        </div>
                        <div className="sectionContent" style={{ maxHeight: workspaceExpanded ? "200px" : "0px", overflowY: "auto" }}>
                            {workspaceFiles.map(f => (
                                <div key={f.filename} className="fileItem">
                                    <svg width="12" height="12" viewBox="0 0 16 16" fill="none" style={{ flexShrink: 0, opacity: 0.5 }}>
                                        <path d="M9 2H4a1 1 0 00-1 1v10a1 1 0 001 1h8a1 1 0 001-1V6L9 2z" stroke="currentColor" strokeWidth="1.2"/>
                                        <path d="M9 2v4h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
                                    </svg>
                                    <a href={getWorkspaceDownloadUrl(f.filename)} download={f.filename} className="fileItemName">
                                        {f.filename}
                                    </a>
                                    <span className="fileItemMeta">{f.size_kb}kb</span>
                                    <button className="deleteBtn" onClick={async () => {
                                        await deleteWorkspaceFile(f.filename);
                                        setWorkspaceFiles(prev => prev.filter(w => w.filename !== f.filename));
                                    }}>✕</button>
                                </div>
                            ))}
                        </div>
                        <div className="sectionDivider" />
                    </>
                )}

                {/* CHATS SECTION */}
                <div className="sectionHeader" onClick={() => setChatsExpanded(p => !p)}>
                    <span className="sectionLabel">Chats</span>
                    <svg className={`sectionToggle ${chatsExpanded ? "open" : ""}`} width="10" height="10" viewBox="0 0 16 16" fill="none">
                        <path d="M6 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                </div>
                <div className="sectionContent chatsScrollArea" style={{ maxHeight: chatsExpanded ? "100%" : "0px", flex: chatsExpanded ? 1 : 0 }}>
                    {conversations.map((c) => (
                        <div
                            key={c.id}
                            className={`chatItem ${c.id === activeId ? "active" : ""}`}
                            onClick={() => switchChat(c.id)}
                        >
                            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" style={{ flexShrink: 0, opacity: 0.5 }}>
                                <path d="M14 10a2 2 0 01-2 2H5l-3 3V4a2 2 0 012-2h8a2 2 0 012 2v6z" stroke="currentColor" strokeWidth="1.2"/>
                            </svg>
                            <span className="chatItemText">{c.title}</span>
                            <button className="deleteBtn" onClick={(e) => {
                                e.stopPropagation();
                                deleteConversation(c.id);
                            }}>✕</button>
                        </div>
                    ))}
                </div>

                {/* STATS */}
                {stats && (
                    <div className="statsPanel">
                        <div className="statRow">
                            <span className="statLabel">RAM</span>
                            <span className="statValue">{stats.ram_used_gb} / {stats.ram_total_gb} GB</span>
                        </div>
                        <div className="statRow">
                            <span className="statLabel">Tier</span>
                            <span className="statValue" style={{
                                color: stats.tier === "high" ? "#7070ee"
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

                {/* Open sidebar button — visible only when collapsed */}
                <button
                    className={`openSidebarBtn ${!sidebarOpen ? "visible" : ""}`}
                    onClick={() => setSidebarOpen(true)}
                    title="Open sidebar"
                >
                    <svg width="11" height="11" viewBox="0 0 16 16" fill="none">
                        <path d="M6 3l5 5-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                </button>

                <div className="chat">
                    {activeConversation?.messages
                        .filter(m => m.content !== "")
                        .map((m, i) => (
                            <MessageBubble key={i} role={m.role} content={m.content} />
                        ))}
                    {showTool && (
                        <div className="thinkingWrapper">
                            <div className="toolStatusBar">{toolStatus}</div>
                            <div className="thinkingDots">
                                <span /><span /><span />
                            </div>
                        </div>
                    )}
                    {showThinking && (
                        <div className="thinkingDots">
                            <span /><span /><span />
                        </div>
                    )}
                    <div ref={chatEndRef} />
                </div>

                {/* Uploaded files panel */}
                {showFiles && uploadedFiles.length > 0 && (
                    <div className="filesPanel">
                        <div className="filesPanelHeader">Uploaded files</div>
                        {uploadedFiles.map(f => (
                            <div key={f} className="fileRow">
                                <svg width="12" height="12" viewBox="0 0 16 16" fill="none" style={{ flexShrink: 0, opacity: 0.5 }}>
                                    <path d="M9 2H4a1 1 0 00-1 1v10a1 1 0 001 1h8a1 1 0 001-1V6L9 2z" stroke="currentColor" strokeWidth="1.2"/>
                                    <path d="M9 2v4h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
                                </svg>
                                <span className="fileName">{f}</span>
                                <button className="deleteBtn" style={{ opacity: 1 }} onClick={() => handleDeleteFile(f)}>✕</button>
                            </div>
                        ))}
                    </div>
                )}

                {/* Input bar */}
                <div className="inputWrapper">
                    <div className="inputRow">
                        <div className="inputActionsLeft">
                            <label className="iconBtn" title="Upload file">
                                <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
                                    <path d="M8 1v9M4 4l4-3 4 3M2 12h12v2H2z" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
                                </svg>
                                <input type="file" hidden onChange={handleUpload} />
                            </label>
                            {totalFiles > 0 && (
                                <button className="fileChip" onClick={() => setShowFiles(p => !p)} title="Show uploaded files">
                                    <svg width="11" height="11" viewBox="0 0 16 16" fill="none">
                                        <path d="M9 2H4a1 1 0 00-1 1v10a1 1 0 001 1h8a1 1 0 001-1V6L9 2z" stroke="currentColor" strokeWidth="1.3"/>
                                        <path d="M9 2v4h4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
                                    </svg>
                                    {totalFiles} file{totalFiles !== 1 ? "s" : ""}
                                </button>
                            )}
                        </div>

                        <textarea
                            ref={textareaRef}
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

                        <button className="sendBtn" onClick={handleSend}>
                            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                                <path d="M2 8h12M10 4l4 4-4 4" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}