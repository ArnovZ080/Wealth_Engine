"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Send, Bell, ShieldCheck } from "lucide-react";

export default function SettingsProfilePage() {
  const [chatId, setChatId] = useState("");
  const [isLinking, setIsLinking] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleLinkTelegram = async () => {
    setIsLinking(true);
    try {
      // Simulate API call to /auth/telegram
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/telegram`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: chatId }),
      });
      if (res.ok) {
        setSuccess(true);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLinking(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Manage your notification and profile alerts.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-white/5 bg-slate-900/50 backdrop-blur-xl">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Send className="h-5 w-5 text-blue-400" />
              <CardTitle>Telegram Notifications</CardTitle>
            </div>
            <CardDescription>
              Link your Telegram account to receive real-time trade signals and Ground Zero alerts.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Telegram Chat ID</label>
              <div className="flex gap-2">
                <Input 
                  placeholder="e.g. 12345678" 
                  value={chatId}
                  onChange={(e) => setChatId(e.target.value)}
                  className="bg-slate-950/50 border-white/10"
                />
                <Button 
                  onClick={handleLinkTelegram} 
                  disabled={isLinking || !chatId}
                  className="bg-blue-600 hover:bg-blue-500 text-white"
                >
                  {isLinking ? "Linking..." : "Link Bot"}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Message @RecursiveFractalBot to get your Chat ID.
              </p>
            </div>

            {success && (
              <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center gap-3">
                <ShieldCheck className="h-5 w-5 text-green-400" />
                <span className="text-sm text-green-400 font-medium">Telegram Linked Successfully!</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-white/5 bg-slate-900/50 backdrop-blur-xl">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-purple-400" />
              <CardTitle>Alert Preferences</CardTitle>
            </div>
            <CardDescription>Configure which events trigger a notification.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-2 rounded hover:bg-white/5 transition-colors">
              <span className="text-sm">Trade Executions (Buy/Sell)</span>
              <Badge className="bg-green-500/20 text-green-400 border-none">Active</Badge>
            </div>
            <div className="flex items-center justify-between p-2 rounded hover:bg-white/5 transition-colors">
              <span className="text-sm">Ground Zero Warnings</span>
              <Badge className="bg-red-500/20 text-red-400 border-none">High Priority</Badge>
            </div>
            <div className="flex items-center justify-between p-2 rounded hover:bg-white/5 transition-colors">
              <span className="text-sm">Weekly Strategy Reports</span>
              <Badge className="bg-blue-500/20 text-blue-400 border-none">Weekly</Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
