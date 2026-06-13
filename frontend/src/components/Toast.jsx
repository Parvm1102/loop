import { createContext, useContext, useState } from "react";
import { CheckCircle, AlertCircle, Info } from "./icons";

const ToastCtx = createContext(null);

const META = {
  success: { Icon: CheckCircle, title: "Success" },
  error: { Icon: AlertCircle, title: "Error" },
  info: { Icon: Info, title: "Info" },
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const push = (msg, level = "info") => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, msg, level }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3500);
  };
  const remove = (id) => setToasts((t) => t.filter((x) => x.id !== id));
  return (
    <ToastCtx.Provider value={{ push, remove }}>
      {children}
      <div className="toast-stack">
        {toasts.map((t) => {
          const { Icon, title } = META[t.level] || META.info;
          return (
            <div
              key={t.id}
              className={`toast ${t.level} no-hover`}
              role="status"
              aria-live="polite"
              onClick={() => remove(t.id)}
            >
              <span className="ticon">
                <Icon size={18} />
              </span>
              <div>
                <div className="ttitle">{title}</div>
                <div className="tmsg">{t.msg}</div>
              </div>
            </div>
          );
        })}
      </div>
    </ToastCtx.Provider>
  );
}

export const useToast = () => useContext(ToastCtx);
