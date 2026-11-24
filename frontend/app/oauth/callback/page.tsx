'use client';

import { useEffect, useState } from 'react';

export default function OAuthCallback() {
  const [message, setMessage] = useState('Completing secure Google sign-in…');

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get('token');
    if (!token) { setMessage('Google sign-in failed. Close this page and try again.'); return; }
    localStorage.setItem('bugsentinelToken', token);
    window.location.replace('/');
  }, []);

  return <main className="shell callback"><section className="panel"><p className="eyebrow">GOOGLE SIGN-IN</p><h1>{message}</h1></section></main>;
}
