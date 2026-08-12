// src/components/ConsentPrompt.tsx
import React from "react";
import { Button } from "./ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "./ui/card";
import { setCookie } from "cookies-next";
import { useNavigate } from "react-router-dom";
import Link from "next/link";
import Chat from "./pages/chat/Chat"; // Importing the Chat component
const ConsentPrompt: React.FC = () => {
    const navigate = useNavigate();

    const handleConsent = () => {
        setCookie("consent_v2", "true", {
            expires: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) // 30 days
        });

        setCookie("visited_v2", "true", {
            expires: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) // 30 days
        });
        window.location.pathname = "/"; // Redirect to the main page or chat page after consent
    };

    const handleDecline = () => {
        setCookie("visited_v2", "true", {
            expires: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) // 30 days
        });
        window.location.href = "https://www.au.dk";
    };

    return (
        <div className="fixed inset-0 backdrop-blur-sm flex items-center justify-center z-50">
            <Card className="w-[550px]">
                <CardHeader>
                    <CardTitle>Consent Form for Using the Customized Chatbot ‘Phil’</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <p>
                        <strong>Research Team, Purpose & Contact information:</strong> This project is conducted by a research team led by Carsten Bergenholtz
                        and Oana Vuculescu (OV) as key members. The research team will process and analyze the data collected. The purpose is to learn from how
                        users engage with the customized chatbot, in order to improve future versions of it as well as potentially publish research based on the
                        analysis. Data may also be analyzed for educational purposes (e.g., student exams) by members of the research team under the same
                        confidentiality conditions.
                    </p>
                    <p>
                        If you have any questions or concerns about the project and the processing of data, please contact OV at oanav@mgmt.au.dk.
                    </p>
                    <p>
                        <strong>Project Support:</strong> This project is supported by It-vest & Aarhus University.
                    </p>
                    <p>
                        <strong>Data Handling:</strong> All data collected in this project is anonymized when storing the data, ensuring your privacy. We track
                        no particular prompt back to any user. The results will be presented in aggregate form, with completely anonymous data. We kindly ask
                        that you do not enter any sensitive or personal information in your interactions with the chatbot.
                    </p>

                    <strong>Consent Acknowledgement:</strong>
                    <p>
                        By selecting "Yes" below, you acknowledge that:
                        <ul className="list-disc pl-6">
                            <li>You understand the purpose of the study and agree to participate.</li>
                            <li>You are aware that your data will be anonymized and that the results will only be presented in an aggregated, anonymous form.</li>
                        </ul>
                    </p>
                    <p>Note, if you do not consent, you can use the version of the customized chatbot we offered in 2024. Please contact OV for a link.</p>
                </CardContent>
                <CardFooter className="flex justify-between">
                    <Button variant="outline" onClick={handleConsent}>
                        Yes, I consent to participate in this study.
                    </Button>
                    <Button variant="outline" onClick={handleDecline}>
                        No, I do not consent to participate in this study.
                    </Button>
                </CardFooter>
            </Card>
        </div>
    );
};

export default ConsentPrompt;
