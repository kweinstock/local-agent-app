/* File: chat.ts
 * Name: Keagan Weinstock
*/

import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

export type Message = {
  role: "user" | "assistant";
  content: string;
};

export type Conversation = {
    id: string;
    title: string;
    messages: Message[];
}

export async function sendMessage(messages: Message[]) {
  const res = await axios.post(`${API_URL}/chat`, {
    messages,
  });

  return res.data.response;
}

export async function loadHistory() {
    const res = await axios.get(`${API_URL}/history`);
    return res.data;
}

export async function saveHistory(conversations: Conversation[]) {
    await axios.post(`${API_URL}/history`, { conversations })
}