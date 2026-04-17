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
        <div className="section-label">Settings</div>
        <h1 className="font-heading text-4xl font-bold tracking-tight">Profile & Alerts</h1>
        <p className="mt-3 text-text-secondary">Manage your notification and profile alerts.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="rv">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Send className="h-5 w-5 text-candle-green" />
              <CardTitle>Telegram Notifications</CardTitle>
            </div>
            <CardDescription>
              Link your Telegram account to receive real-time trade signals and Ground Zero alerts.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-widest text-text-muted font-semibold">Telegram Chat ID</label>
              <div className="flex gap-2">
                <Input 
                  placeholder="e.g. 12345678" 
                  value={chatId}
                  onChange={(e) => setChatId(e.target.value)}
                  className="flex-1"
                />
                <Button 
                  onClick={handleLinkTelegram} 
                  disabled={isLinking || !chatId}
                >
                  {isLinking ? "Linking..." : "Link Bot"}
                </Button>
              </div>
              <p className="text-xs text-text-secondary">
                Message @RecursiveFractalBot to get your Chat ID.
              </p>
            </div>

            {success && (
              <div className="p-3 rounded-xl bg-candle-green/10 border border-candle-green/20 flex items-center gap-3">
                <ShieldCheck className="h-5 w-5 text-candle-green" />
                <span className="text-sm text-candle-green font-medium">Telegram Linked Successfully!</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="rv">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-purple-400" />
              <CardTitle>Alert Preferences</CardTitle>
            </div>
            <CardDescription>Configure which events trigger a notification.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-xl hover:bg-white/5 transition-colors">
              <span className="text-sm">Trade Executions (Buy/Sell)</span>
              <Badge className="bg-candle-green/20 text-candle-green border-none">Active</Badge>
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl hover:bg-white/5 transition-colors">
              <span className="text-sm">Ground Zero Warnings</span>
              <Badge className="bg-candle-red/20 text-candle-red border-none">High Priority</Badge>
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl hover:bg-white/5 transition-colors">
              <span className="text-sm">Weekly Strategy Reports</span>
              <Badge className="bg-white/10 text-text-secondary border border-white/10">Weekly</Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
