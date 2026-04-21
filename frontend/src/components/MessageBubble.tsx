/* File: MessageBubble.tsx
 * Name: Keagan Weinstock
*/

import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

type Props = {
    role: "user" | "assistant";
    content: string;
};

export default function MessageBubble({ role, content }: Props) {
    return (
        <div className={`msg ${role}`}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}