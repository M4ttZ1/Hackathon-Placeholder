import React from 'react'
import { Link } from 'react-router-dom';

const GetStarted = () => {
  return (
    <>
    <h1>Welcome to The Phish Scanner app</h1>
    <div>This app will help you identify possible phishing emails</div>
    <div>Click on the "Get Started" button to get started</div>
    <Link to="/home">
        <button>Get Started</button>
    </Link>
    </>
  )
}

export default GetStarted