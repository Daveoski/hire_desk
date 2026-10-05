"use client";

import { CalendarCheck, CalendarPlus } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useGoogleConnect, useGoogleDisconnect, useGoogleStatus } from "@/lib/queries";

// Interviews scheduled while connected are pushed to Google Calendar
// (with the interviewer as attendee) and deleted when cancelled.
export function GoogleCalendarCard() {
  const status = useGoogleStatus();
  const connect = useGoogleConnect();
  const disconnect = useGoogleDisconnect();
  const connected = status.data?.connected ?? false;

  return (
    <Card>
      <CardContent className="flex flex-wrap items-center gap-3">
        <div className="min-w-0 flex-1">
          <p className="flex items-center gap-2 font-semibold">
            <CalendarCheck className="size-4 text-muted-foreground" />
            Google Calendar
            {connected && <Badge className="bg-stage-hired/15 text-stage-hired">Connected</Badge>}
          </p>
          <p className="text-sm text-muted-foreground">
            Interviews you schedule are added to your Google Calendar and removed when cancelled.
          </p>
        </div>
        {status.isLoading ? (
          <Skeleton className="h-9 w-28" />
        ) : connected ? (
          <Button
            variant="outline"
            size="sm"
            disabled={disconnect.isPending}
            onClick={() => disconnect.mutate(undefined, { onError: (error) => toast.error(error.message) })}
          >
            {disconnect.isPending ? "Disconnecting..." : "Disconnect"}
          </Button>
        ) : (
          <Button
            size="sm"
            disabled={connect.isPending}
            onClick={() =>
              connect.mutate(undefined, {
                onError: (error) =>
                  toast.error(error.message, { description: "Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to enable it." }),
              })
            }
          >
            <CalendarPlus />
            {connect.isPending ? "Opening Google..." : "Connect"}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
