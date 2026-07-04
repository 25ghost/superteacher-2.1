import AdminWorkspace from "./components/AdminWorkspace";
import PublicMapExperience from "./components/PublicMapExperience";

export default function App() {
  const route = window.location.pathname.replace(/\/+$/, "") || "/";
  return route === "/admin" ? <AdminWorkspace /> : <PublicMapExperience />;
}

