#!/usr/bin/env bash
set -euo pipefail

require_root() {
  if [[ $EUID -ne 0 ]]; then
    echo "Please run as root (use sudo)." >&2
    exit 1
  fi
}

prompt() {
  local _q="$1"
  local _def="${2:-}"
  local _ans
  if [[ -n "$_def" ]]; then
    read -e -p "$_q [$_def]: " _ans || true
    echo "${_ans:-$_def}"
  else
    read -e -p "$_q " _ans || true
    echo "$_ans"
  fi
}

confirm_yn() {
  local _q="$1"
  local _def="${2:-Y}"
  local _dchar
  if [[ "$_def" == [Yy]* ]]; then _dchar="Y/n"; else _dchar="y/N"; fi
  local _ans
  read -e -p "$_q (${_dchar}): " _ans || true
  _ans="${_ans:-$_def}"
  [[ "$_ans" == [Yy]* ]]
}

dedupe_csv() {
  awk -v RS=, '{
    if (!seen[$0]++) out = out (out ? "," : "") $0
  } END { print out }' <<<"$1"
}

main() {
  require_root

  local default_shell="/bin/bash"
  local default_clone=""
  id -u pi &>/dev/null && default_clone="pi"

  echo "=== Add New RPi User (interactive) ==="

  local NEWUSER
  while :; do
    NEWUSER="$(prompt "New username:" "")"
    [[ -n "$NEWUSER" ]] && break
    echo "Username cannot be empty."
  done

  local HOME_DIR
  HOME_DIR="$(prompt "Home directory (leave blank for default)" "/home/$NEWUSER")"

  local CLONE_FROM
  CLONE_FROM="$(prompt "Clone groups from user (blank to skip)" "$default_clone")"
  [[ "$CLONE_FROM" == "-" ]] && CLONE_FROM=""

  local EXTRA_GROUPS
  EXTRA_GROUPS="$(prompt "Extra groups (comma-separated, blank to skip)" "")"

  local SHELL_BIN
  SHELL_BIN="$(prompt "Login shell" "$default_shell")"
  if ! grep -qx "$SHELL_BIN" /etc/shells; then
    echo "Shell $SHELL_BIN not valid. Aborting." >&2
    exit 1
  fi

  local WANT_SUDO
  confirm_yn "Add user to sudo group?" "Y" && WANT_SUDO=1 || WANT_SUDO=0

  local PW_PROMPT
  confirm_yn "Set a password now?" "Y" && PW_PROMPT=1 || PW_PROMPT=0

  local SSH_PUBKEY_PATH
  SSH_PUBKEY_PATH="$(prompt "Path to SSH public key (blank to skip)" "")"
  [[ -n "$SSH_PUBKEY_PATH" && ! -f "$SSH_PUBKEY_PATH" ]] && SSH_PUBKEY_PATH=""

  local PWLESS_SUDO
  confirm_yn "Enable passwordless sudo (NOPASSWD)?" "N" && PWLESS_SUDO=1 || PWLESS_SUDO=0

  echo
  echo "--- Summary ---"
  echo "User:     $NEWUSER"
  echo "Home:     $HOME_DIR"
  echo "Clone:    ${CLONE_FROM:-<none>}"
  echo "Groups:   ${EXTRA_GROUPS:-<none>}"
  echo "Shell:    $SHELL_BIN"
  echo "Sudo:     $([[ $WANT_SUDO -eq 1 ]] && echo yes || echo no)"
  echo "Password: $([[ $PW_PROMPT -eq 1 ]] && echo yes || echo no)"
  echo "SSH key:  ${SSH_PUBKEY_PATH:-<none>}"
  echo "PWless:   $([[ $PWLESS_SUDO -eq 1 ]] && echo yes || echo no)"
  echo

  confirm_yn "Proceed?" "Y" || exit 0

  # --- build group list ---
  declare -a GROUPS_SET=()
  if [[ -n "$CLONE_FROM" ]] && id "$CLONE_FROM" &>/dev/null; then
    mapfile -t CLONE_GROUPS < <(id -nG "$CLONE_FROM" | tr ' ' '\n')
    local CLONE_PRIMARY
    CLONE_PRIMARY="$(id -gn "$CLONE_FROM")"
    for g in "${CLONE_GROUPS[@]}"; do
      [[ "$g" == "$CLONE_PRIMARY" ]] && continue
      GROUPS_SET+=("$g")
    done
  fi
  if [[ -n "$EXTRA_GROUPS" ]]; then
    IFS=',' read -r -a EXTRA_ARR <<<"$EXTRA_GROUPS"
    GROUPS_SET+=("${EXTRA_ARR[@]}")
  fi
  [[ $WANT_SUDO -eq 1 ]] && GROUPS_SET+=("sudo")

  local GROUPS_CSV=""
  if [[ ${#GROUPS_SET[@]} -gt 0 ]]; then
    GROUPS_CSV="$(printf "%s\n" "${GROUPS_SET[@]}" | awk '!seen[$0]++' | paste -sd, -)"
  fi

  # --- create user ---
  if id "$NEWUSER" &>/dev/null; then
    echo "User already exists. Skipping creation."
  else
    adduser --disabled-password --gecos "" --home "$HOME_DIR" --shell "$SHELL_BIN" "$NEWUSER"
  fi

  [[ -n "$GROUPS_CSV" ]] && usermod -aG "$GROUPS_CSV" "$NEWUSER"

  [[ $PW_PROMPT -eq 1 ]] && passwd "$NEWUSER"

  if [[ -n "$SSH_PUBKEY_PATH" ]]; then
    install -d -m 700 -o "$NEWUSER" -g "$NEWUSER" "$HOME_DIR/.ssh"
    install -m 600 -o "$NEWUSER" -g "$NEWUSER" /dev/null "$HOME_DIR/.ssh/authorized_keys"
    cat "$SSH_PUBKEY_PATH" >> "$HOME_DIR/.ssh/authorized_keys"
    chown "$NEWUSER:$NEWUSER" "$HOME_DIR/.ssh/authorized_keys"
    echo "SSH key installed."
  fi

  if [[ $PWLESS_SUDO -eq 1 ]]; then
    echo "${NEWUSER} ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/99-${NEWUSER}-nopasswd"
    chmod 440 "/etc/sudoers.d/99-${NEWUSER}-nopasswd"
    visudo -cf "/etc/sudoers.d/99-${NEWUSER}-nopasswd" || rm -f "/etc/sudoers.d/99-${NEWUSER}-nopasswd"
  fi

    # add to sudo group if needed
    sudo usermod -aG sudo pymirror

    # create a drop-in that allows passwordless sudo for this user
    echo 'pymirror ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/99-pymirror-nopasswd >/dev/null
    sudo chmod 440 /etc/sudoers.d/99-pymirror-nopasswd
    sudo visudo -cf /etc/sudoers.d/99-pymirror-nopasswd

  echo "User $NEWUSER created with home $HOME_DIR."
}

main "$@"
