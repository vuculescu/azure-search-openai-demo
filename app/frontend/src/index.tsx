import React from "react";
import ReactDOM from "react-dom/client";
import { createHashRouter, RouterProvider } from "react-router-dom";
import { I18nextProvider } from "react-i18next";
import { HelmetProvider } from "react-helmet-async";
import { initializeIcons } from "@fluentui/react";
import ConsentPrompt from "./ConsentPrompt"; // Import the ConsentPrompt component

import "./index.css";

import Chat from "./pages/chat/Chat";
import LayoutWrapper from "./layoutWrapper";
import i18next from "./i18n/config";

initializeIcons();
const router = createHashRouter([
    {
        path: "/",
        element: <LayoutWrapper />,
        children: [
            {
                index: true,
                element: <Chat />
            },
            {
                path: "consent",
                element: <ConsentPrompt /> // Add the path for the consent page
            },
            {
                path: "qa",
                lazy: () => import("./pages/ask/Ask")
            },
            {
                path: "*",
                lazy: () => import("./pages/NoPage")
            }
        ]
    }
]);

const RootElement: React.FC = () => {
    return <RouterProvider router={router} />;
};

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
        <HelmetProvider>
            <RootElement />
        </HelmetProvider>
    </React.StrictMode>
);
