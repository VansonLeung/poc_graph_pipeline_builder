"use strict"

const COLORS = {
  reset: "\x1b[0m",
  gray: "\x1b[90m",
  blue: "\x1b[34m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  red: "\x1b[31m",
}

function timestamp() {
  return new Date().toISOString()
}

function format(message, color) {
  return `${COLORS.gray}${timestamp()}${COLORS.reset} ${color}${message}${COLORS.reset}`
}

const logger = {
  heading(message) {
    console.log("")
    console.log(format(`== ${message} ==`, COLORS.blue))
  },
  info(message) {
    console.log(format(message, COLORS.blue))
  },
  success(message) {
    console.log(format(message, COLORS.green))
  },
  warn(message) {
    console.warn(format(message, COLORS.yellow))
  },
  error(message) {
    console.error(format(message, COLORS.red))
  },
  detail(message) {
    console.log(format(`  • ${message}`, COLORS.gray))
  },
  step(label) {
    console.log(format(label, COLORS.blue))
  },
  divider() {
    console.log(format("----------------------------------------", COLORS.gray))
  },
}

module.exports = { logger }
