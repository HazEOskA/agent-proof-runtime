import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as apr from "../api/aprClient";
import { drainAprEvent, enqueueAprEvents } from "./runtimeEventAdapter";
import { TERMINAL_STATES, type AprRunDetail } from "./types";
import {
  applySessionSnapshot,
  initialWorldState,
  missionStoneState,
  pushLog,
  resetMission,
  type WorldState,
} from "./worldState";

const HEALTH_INTERVAL_MS = 4000;
const SESSION_INTERVAL_MS = 500;
/**
 * Playback rate for recorded APR events. The runtime decides what happened;
 * this only decides how fast the world is allowed to show it.
 */
const DRAIN_INTERVAL_MS = 260;

export interface RuntimeApi {
  world: WorldState;
  stone: ReturnType<typeof missionStoneState>;
  runDetail: AprRunDetail | null;
  starting: boolean;
  startError: string | null;
  startMission: (brief: string, provider: string) => Promise<boolean>;
  clearStartError: () => void;
}

export function useRuntime(): RuntimeApi {
  const [world, setWorld] = useState<WorldState>(initialWorldState);
  const [runDetail, setRunDetail] = useState<AprRunDetail | null>(null);
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const sessionRef = useRef<string | null>(null);
  const terminalRef = useRef(false);

  // Runtime connectivity. Without a healthy APR nothing in the world moves.
  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();
    const check = async () => {
      let healthy = false;
      try {
        healthy = await apr.health(controller.signal);
      } catch {
        if (cancelled) return;
      }
      if (cancelled) return;
      setWorld((state) => {
        const next = healthy ? "ONLINE" : "OFFLINE";
        if (state.connection === next) return state;
        return pushLog({ ...state, connection: next }, {
          worldEvent: next === "ONLINE" ? "MISSION_ACCEPTED" : "MISSION_FAILED",
          label: next === "ONLINE" ? "Połączono z APR" : "APR niedostępny — RUNTIME OFFLINE",
          tone: next === "ONLINE" ? "good" : "bad",
        });
      });
    };
    void check();
    const timer = window.setInterval(() => void check(), HEALTH_INTERVAL_MS);
    return () => {
      cancelled = true;
      controller.abort();
      window.clearInterval(timer);
    };
  }, []);

  // Session polling. Stops on a terminal runtime state — no idle traffic.
  useEffect(() => {
    if (!world.sessionId || terminalRef.current) return undefined;
    const sessionId = world.sessionId;
    let cancelled = false;
    const controller = new AbortController();

    const poll = async () => {
      try {
        const session = await apr.readSession(sessionId, controller.signal);
        if (cancelled) return;
        setWorld((state) => {
          if (state.sessionId !== sessionId) return state;
          const withSnapshot = applySessionSnapshot({ ...state, connection: "ONLINE" }, session);
          const withEvents = enqueueAprEvents(withSnapshot, session.events);
          if (TERMINAL_STATES.has(session.state)) {
            terminalRef.current = true;
            return {
              ...withEvents,
              terminalMissionStatus:
                session.mission_status ?? (session.state === "failed" ? "FAILED" : null),
            };
          }
          return withEvents;
        });
      } catch (error) {
        if (cancelled || (error as Error).name === "AbortError") return;
        if (error instanceof apr.AprOfflineError) {
          setWorld((state) => ({ ...state, connection: "OFFLINE" }));
        }
      }
    };

    void poll();
    const timer = window.setInterval(() => {
      if (terminalRef.current) {
        window.clearInterval(timer);
        return;
      }
      void poll();
    }, SESSION_INTERVAL_MS);
    return () => {
      cancelled = true;
      controller.abort();
      window.clearInterval(timer);
    };
  }, [world.sessionId, world.runtimeState]);

  // Recorded events are played back one at a time so the world stays readable.
  useEffect(() => {
    const timer = window.setInterval(() => {
      setWorld((state) => {
        if (state.pending.length > 0) return drainAprEvent(state);
        if (state.terminalMissionStatus === null) return state;
        const execution =
          state.terminalMissionStatus === "PASSED"
            ? "COMPLETED"
            : state.terminalMissionStatus === "FAILED"
              ? "FAILED"
              : state.execution;
        return { ...state, execution, terminalMissionStatus: null };
      });
    }, DRAIN_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, []);

  // Proof Bundle is read only once the runtime reported a run id.
  useEffect(() => {
    if (!world.runId || world.proof === "NONE" || world.proof === "PENDING") return undefined;
    let cancelled = false;
    const controller = new AbortController();
    void (async () => {
      try {
        const detail = await apr.readRun(world.runId as string, controller.signal);
        if (!cancelled) setRunDetail(detail);
      } catch {
        /* the world keeps the verifier result it already has */
      }
    })();
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [world.runId, world.proof]);

  const startMission = useCallback(async (brief: string, provider: string): Promise<boolean> => {
    setStarting(true);
    setStartError(null);
    try {
      const session = await apr.startMission({
        mission_type: "verified_website_build",
        brief,
        provider,
      });
      terminalRef.current = false;
      sessionRef.current = session.session_id;
      setRunDetail(null);
      setWorld((state) => {
        const fresh = resetMission(state);
        const withSnapshot = applySessionSnapshot(fresh, session);
        return enqueueAprEvents(withSnapshot, session.events);
      });
      return true;
    } catch (error) {
      setStartError(
        error instanceof apr.AprOfflineError
          ? "Nie mogę uruchomić misji — APR jest niedostępny."
          : (error as Error).message,
      );
      return false;
    } finally {
      setStarting(false);
    }
  }, []);

  const stone = useMemo(() => missionStoneState(world), [world]);

  return {
    world,
    stone,
    runDetail,
    starting,
    startError,
    startMission,
    clearStartError: useCallback(() => setStartError(null), []),
  };
}
