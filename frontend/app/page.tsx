import { redirect } from 'next/navigation';

export default function RootPage() {
  // Simple entry point, will be intercepted by router or dashboard layout logic
  redirect('/dashboard');
}
