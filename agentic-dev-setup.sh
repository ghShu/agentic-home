#!/usr/bin/env bash
# agentic-dev-setup.sh — Agentic development environment setup (macOS + Linux)
# Usage:
#   ./agentic-dev-setup.sh              # run all steps
#   ./agentic-dev-setup.sh --from STEP  # resume from a specific step
#   ./agentic-dev-setup.sh STEP [STEP]  # run specific step(s)
#   ./agentic-dev-setup.sh --help
VERSION=1.0.0

set -euo pipefail

# Allow --help and --version without an interactive terminal
case "${1:-}" in
  --help|-h|--version|-v) ;;
  *)
    if [ ! -t 0 ]; then
      echo "ERROR: This script must be run in an interactive terminal."
      exit 1
    fi
    ;;
esac

# ─── Colors & Logging ─────────────────────────────────────────────────────────
GREEN='\033[0;32m'
BGREEN='\033[1;32m'
BROWN='\033[0;33m'
BBROWN='\033[1;33m'
RED='\033[0;31m'
BRED='\033[1;31m'
BOLD='\033[1m'
NC='\033[0m'

OUTPUT_FILE="/tmp/agentic-dev-setup-$(date '+%F-%T').log"
PID_FILE="/tmp/mac_setup_sudo_cache"

echo_t() { printf "\n${BOLD}$(date)  -->${NC} $*\n" | tee -a "$OUTPUT_FILE"; }
echo_i() { printf "${BOLD}  -->${NC} $*\n"           | tee -a "$OUTPUT_FILE"; }
echo_w() { printf "\n${BBROWN}  --> WARN:${NC} $*\n" | tee -a "$OUTPUT_FILE"; }
echo_e() { printf "\n${BRED}  --> ERROR:${NC} $*\n"  | tee -a "$OUTPUT_FILE"; }
echo_ask() { printf "${BGREEN}  --> $*${NC}\n"; }

_confirm_choice() {
  local prompt="$1"
  local response
  while true; do
    echo
    echo_ask "$prompt [Y/N]"
    read -r response
    case $response in
      [yY][eE][sS]|[yY]) return 0 ;;
      [nN][oO]|[nN])     return 1 ;;
      *) printf "${RED}Please answer yes or no.${NC}\n" ;;
    esac
  done
}

SUDO_LOOP_PID=""

_cleanup() {
  rm -f "$PID_FILE" >/dev/null 2>&1
  [ -n "$SUDO_LOOP_PID" ] && kill "$SUDO_LOOP_PID" 2>/dev/null || true
}

_ensure_sudo() {
  if [ -f "$PID_FILE" ]; then return 0; fi
  echo_i "Requesting sudo — you may be prompted for your password:"
  echo $$ >> "$PID_FILE"
  trap '_cleanup' EXIT
  sudo -v
  # Keep sudo alive in background; sleep first so we kill it cleanly on exit
  while [ -f "$PID_FILE" ]; do sleep 30; sudo -v; done &
  SUDO_LOOP_PID=$!
}

_command_exists() { command -v "$1" >/dev/null 2>&1; }

_brew_installed() { brew list "$1" >/dev/null 2>&1; }

_brew_cask_installed() { brew list --cask "$1" >/dev/null 2>&1; }

# Ensure brew is on PATH (needed after installation and on Apple Silicon)
_load_brew() {
  if _command_exists brew; then return 0; fi
  if [ -f /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [ -f /usr/local/bin/brew ]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
}

# Source nvm from Homebrew (macOS) or standard install dir (Linux)
_load_nvm() {
  export NVM_DIR="$HOME/.nvm"
  local _nvm_sh
  for _nvm_sh in "/opt/homebrew/opt/nvm/nvm.sh" "$NVM_DIR/nvm.sh"; do
    [ -s "$_nvm_sh" ] && { source "$_nvm_sh"; return 0; }
  done
}

# ─── OS / Distro Detection ────────────────────────────────────────────────────
OS="$(uname -s)"   # Darwin or Linux

PKG_MANAGER=""
if [ "$OS" = "Linux" ]; then
  if   _command_exists apt-get; then PKG_MANAGER="apt"
  elif _command_exists dnf;     then PKG_MANAGER="dnf"
  elif _command_exists yum;     then PKG_MANAGER="yum"
  elif _command_exists pacman;  then PKG_MANAGER="pacman"
  else
    echo_w "No supported package manager found (apt/dnf/yum/pacman). Some steps may be skipped."
    PKG_MANAGER="unknown"
  fi
fi

# Install a package using the platform's package manager
install_pkg() {
  local pkg="$1"
  if [ "$OS" = "Darwin" ]; then
    _brew_installed "$pkg" && return 0
    brew install "$pkg" >> "$OUTPUT_FILE" 2>&1
  elif [ "$PKG_MANAGER" = "apt" ]; then
    sudo apt-get install -y "$pkg" >> "$OUTPUT_FILE" 2>&1
  elif [ "$PKG_MANAGER" = "dnf" ] || [ "$PKG_MANAGER" = "yum" ]; then
    sudo "$PKG_MANAGER" install -y "$pkg" >> "$OUTPUT_FILE" 2>&1
  elif [ "$PKG_MANAGER" = "pacman" ]; then
    sudo pacman -S --noconfirm "$pkg" >> "$OUTPUT_FILE" 2>&1
  else
    echo_w "No supported package manager — skipping $pkg"
  fi
}

# ─── Steps ────────────────────────────────────────────────────────────────────

check_prereqs() {
  echo_t "Checking prerequisites"

  if [ "$OS" = "Darwin" ]; then
    echo_i "Checking Xcode Command Line Tools..."
    if xcode-select -p &>/dev/null; then
      echo_i "Xcode CLT already installed — skipping"
    else
      echo_i "Installing Xcode Command Line Tools (a popup may appear)..."
      xcode-select --install 2>/dev/null || true
      echo_ask "Press ENTER once the Xcode CLT installation popup has completed."
      read -r
      _ensure_sudo
      sudo xcodebuild -license accept >> "$OUTPUT_FILE" 2>&1 || true
    fi
  else
    echo_i "Ensuring build essentials are installed..."
    _ensure_sudo
    if [ "$PKG_MANAGER" = "apt" ]; then
      sudo apt-get update -qq >> "$OUTPUT_FILE" 2>&1
      sudo apt-get install -y curl git build-essential >> "$OUTPUT_FILE" 2>&1
    elif [ "$PKG_MANAGER" = "pacman" ]; then
      sudo pacman -Sy --noconfirm base-devel git curl >> "$OUTPUT_FILE" 2>&1
    elif [ "$PKG_MANAGER" = "dnf" ] || [ "$PKG_MANAGER" = "yum" ]; then
      sudo "$PKG_MANAGER" groupinstall -y "Development Tools" >> "$OUTPUT_FILE" 2>&1
      sudo "$PKG_MANAGER" install -y curl git >> "$OUTPUT_FILE" 2>&1
    fi
  fi

  mkdir -p ~/.ssh
  echo_i "Prerequisites OK"
}

fix_ssh_permissions() {
  echo_t "Fixing SSH key permissions"

  chmod 700 ~/.ssh

  # Private keys should be 600 (owner read/write only)
  for key in ~/.ssh/id_rsa ~/.ssh/id_ed25519 ~/.ssh/id_ed25519_ghshu ~/.ssh/id_ed25519_jetson ~/.ssh/rsa_key.pem; do
    if [ -f "$key" ]; then
      chmod 600 "$key"
      echo_i "Set 600 on $key"
    fi
  done

  # Public keys can be 644
  for pubkey in ~/.ssh/*.pub; do
    [ -f "$pubkey" ] && chmod 644 "$pubkey"
  done

  echo_i "SSH permissions fixed"
  echo_i "Testing GitHub SSH access (using gshu host alias)..."
  ssh -T gshu 2>&1 | head -2 || true
}

setup_package_manager() {
  if [ "$OS" = "Darwin" ]; then
    echo_t "Setting up Homebrew"

    _load_brew
    if _command_exists brew; then
      echo_i "Homebrew already installed — updating..."
      brew update >> "$OUTPUT_FILE" 2>&1
    else
      echo_i "Installing Homebrew..."
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      _load_brew
      if ! _command_exists brew; then
        echo_e "Homebrew installation failed — check output above"
        exit 1
      fi
    fi

    echo_i "Running brew doctor..."
    if ! brew doctor >> "$OUTPUT_FILE" 2>&1; then
      echo_w "brew doctor reported warnings — check $OUTPUT_FILE for details"
    fi

    # Fix zsh compinit insecure directories warning
    if [ -d /opt/homebrew/share ]; then
      chmod -R go-w /opt/homebrew/share 2>/dev/null || true
    fi

    echo_i "Homebrew ready"
  else
    echo_t "Updating package manager ($PKG_MANAGER)"
    _ensure_sudo
    if [ "$PKG_MANAGER" = "apt" ]; then
      sudo apt-get update -qq >> "$OUTPUT_FILE" 2>&1
      echo_i "apt updated"
    elif [ "$PKG_MANAGER" = "dnf" ] || [ "$PKG_MANAGER" = "yum" ]; then
      sudo "$PKG_MANAGER" check-update >> "$OUTPUT_FILE" 2>&1 || true
      echo_i "$PKG_MANAGER updated"
    elif [ "$PKG_MANAGER" = "pacman" ]; then
      sudo pacman -Sy >> "$OUTPUT_FILE" 2>&1
      echo_i "pacman synced"
    else
      echo_w "Unknown package manager — skipping update"
    fi
  fi
}

_configure_linux_terminal_font() {
  local font="JetBrainsMono Nerd Font Mono"
  local font_size=12

  # Priority 1: GNOME (Ubuntu default — gnome-terminal uses system monospace font)
  if _command_exists gsettings; then
    gsettings set org.gnome.desktop.interface monospace-font-name "$font $font_size"
    echo_i "Set monospace font via gsettings (gnome-terminal will pick this up)"

  # Priority 2: kitty
  elif [ -d "$HOME/.config/kitty" ]; then
    local conf="$HOME/.config/kitty/kitty.conf"
    if ! grep -q "font_family" "$conf" 2>/dev/null; then
      echo "font_family $font" >> "$conf"
      echo_i "Added font_family to ~/.config/kitty/kitty.conf"
    else
      echo_i "kitty font_family already set — skipping"
    fi

  # Priority 3: alacritty
  elif [ -d "$HOME/.config/alacritty" ]; then
    local conf="$HOME/.config/alacritty/alacritty.toml"
    if [ ! -f "$conf" ] || ! grep -q "\[font\]" "$conf" 2>/dev/null; then
      printf '\n[font]\n[font.normal]\nfamily = "%s"\n' "$font" >> "$conf"
      echo_i "Added font config to ~/.config/alacritty/alacritty.toml"
    else
      echo_i "alacritty font already configured — skipping"
    fi

  else
    echo_ask "Set your terminal font to '$font' for Starship glyphs to render correctly."
  fi
}

install_terminal() {
  if [ "$OS" = "Darwin" ]; then
    echo_t "Installing Ghostty terminal"
    _load_brew

    if _brew_cask_installed ghostty; then
      echo_i "Ghostty already installed — skipping"
      return 0
    fi

    brew install --cask ghostty >> "$OUTPUT_FILE" 2>&1
    echo_i "Ghostty installed"

    mkdir -p ~/.config/ghostty
    if [ ! -f ~/.config/ghostty/config ]; then
      cat > ~/.config/ghostty/config << 'EOF'
# Ghostty config — edit as needed
font-family = "JetBrains Mono"
font-size = 14
theme = "Catppuccin Mocha"
window-decoration = false
window-padding-x = 8
window-padding-y = 6
shell-integration = zsh
copy-on-select = true
EOF
      echo_i "Wrote default Ghostty config to ~/.config/ghostty/config"
    else
      echo_i "Ghostty config already exists — skipping"
    fi
  else
    echo_t "Configuring terminal font (Linux)"
    _configure_linux_terminal_font
  fi
}

install_nerd_font() {
  echo_t "Installing JetBrains Mono Nerd Font (for Starship glyphs)"

  if [ "$OS" = "Darwin" ]; then
    _load_brew
    if ls ~/Library/Fonts/JetBrainsMono* >/dev/null 2>&1; then
      echo_i "JetBrains Mono already installed — skipping"
      return 0
    fi
    brew install --cask font-jetbrains-mono-nerd-font >> "$OUTPUT_FILE" 2>&1
    echo_i "JetBrains Mono Nerd Font installed"
    echo_ask "Set the font in Ghostty config: font-family = \"JetBrainsMono Nerd Font\""
  else
    local font_dir="$HOME/.local/share/fonts"
    if ls "$font_dir"/JetBrainsMono* >/dev/null 2>&1; then
      echo_i "JetBrains Mono already installed — skipping"
      return 0
    fi
    mkdir -p "$font_dir"
    echo_i "Downloading JetBrains Mono Nerd Font..."
    curl -fLo "$font_dir/JetBrainsMonoNerdFontMono-Regular.ttf" \
      "https://github.com/ryanoasis/nerd-fonts/raw/HEAD/patched-fonts/JetBrainsMono/Ligatures/Regular/JetBrainsMonoNerdFontMono-Regular.ttf" \
      >> "$OUTPUT_FILE" 2>&1
    fc-cache -fv >> "$OUTPUT_FILE" 2>&1
    echo_i "JetBrains Mono Nerd Font installed to $font_dir"
  fi
}

setup_shell() {
  echo_t "Setting up shell (oh-my-zsh + Starship + plugins)"

  # oh-my-zsh
  if [ -d ~/.oh-my-zsh ]; then
    echo_i "oh-my-zsh already installed — skipping"
  else
    echo_i "Installing oh-my-zsh..."
    RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" >> "$OUTPUT_FILE" 2>&1
    echo_i "oh-my-zsh installed"
  fi

  _load_brew

  # Starship prompt
  if _command_exists starship; then
    echo_i "Starship already installed — skipping"
  else
    echo_i "Installing Starship..."
    if [ "$OS" = "Darwin" ]; then
      _load_brew
      brew install starship >> "$OUTPUT_FILE" 2>&1
    else
      # Official install script works on all Linux distros
      curl -sS https://starship.rs/install.sh | sh -s -- --yes >> "$OUTPUT_FILE" 2>&1
    fi
    echo_i "Starship installed"
  fi

  # zsh-autosuggestions
  local autosuggest_dir="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-autosuggestions"
  if [ -d "$autosuggest_dir" ]; then
    echo_i "zsh-autosuggestions already installed"
  else
    echo_i "Installing zsh-autosuggestions..."
    git clone https://github.com/zsh-users/zsh-autosuggestions "$autosuggest_dir" >> "$OUTPUT_FILE" 2>&1
  fi

  # fast-syntax-highlighting
  local fsh_dir="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/fast-syntax-highlighting"
  if [ -d "$fsh_dir" ]; then
    echo_i "fast-syntax-highlighting already installed"
  else
    echo_i "Installing fast-syntax-highlighting..."
    git clone https://github.com/zdharma-continuum/fast-syntax-highlighting "$fsh_dir" >> "$OUTPUT_FILE" 2>&1
  fi

  echo_i "Shell plugins installed"
}

write_zshrc() {
  echo_t "Writing clean ~/.zshrc"

  if [ -f ~/.zshrc ]; then
    echo_w "~/.zshrc already exists — skipping to preserve your customizations."
    echo_w "Ensure the following are present in your ~/.zshrc:"
    echo_w "  \$HOME/bin and \$HOME/.local/bin in PATH"
    echo_w "  nvm sourced from \$NVM_DIR/nvm.sh or Homebrew path"
    echo_w "  Starship init: eval \"\$(starship init zsh)\""
    echo_w "  Credentials: source ~/.anthropic.env and ~/.github.env if they exist"
    return 0
  fi

  cat > ~/.zshrc << 'ZSHRC'
# ~/.zshrc

# ─── PATH ─────────────────────────────────────────────────────────────────────
export PATH="$HOME/bin:$HOME/.local/bin:/usr/local/bin:$PATH"

# ─── oh-my-zsh ────────────────────────────────────────────────────────────────
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME=""  # Starship handles the prompt
plugins=(git zsh-autosuggestions fast-syntax-highlighting)
source "$ZSH/oh-my-zsh.sh"

# ─── Starship prompt ──────────────────────────────────────────────────────────
eval "$(starship init zsh)"

# ─── NVM (Node Version Manager) ───────────────────────────────────────────────
export NVM_DIR="$HOME/.nvm"
for _nvm_sh in "/opt/homebrew/opt/nvm/nvm.sh" "$NVM_DIR/nvm.sh"; do
  [ -s "$_nvm_sh" ] && { source "$_nvm_sh"; break; }
done
unset _nvm_sh

# ─── uv (Python) ──────────────────────────────────────────────────────────────
[ -f "$HOME/.local/bin/uv" ] && eval "$(uv generate-shell-completion zsh 2>/dev/null)"

# ─── Private credentials (never commit these files) ───────────────────────────
# Store tokens in separate env files:
#   ~/.anthropic.env  → export ANTHROPIC_API_KEY=sk-ant-...
#   ~/.github.env     → export GITHUB_TOKEN=ghp_...
[[ -f "$HOME/.anthropic.env" ]] && source "$HOME/.anthropic.env"
[[ -f "$HOME/.github.env" ]]    && source "$HOME/.github.env"
ZSHRC

  echo_i "~/.zshrc written"
  echo_ask "IMPORTANT: Move your GITHUB_TOKEN out of .zshrc into ~/.github.env"
  echo_ask "  echo 'export GITHUB_TOKEN=your_token_here' > ~/.github.env && chmod 600 ~/.github.env"
}

install_dev_tools() {
  echo_t "Installing developer tools"

  if [ "$OS" = "Darwin" ]; then
    _load_brew
  fi

  # Package names are the same across brew/apt for these tools
  local tools=(git gh jq wget tree bat fd ripgrep fzf)
  for tool in "${tools[@]}"; do
    if _command_exists "$tool"; then
      echo_i "$tool already installed — skipping"
    else
      echo_i "Installing $tool..."
      install_pkg "$tool"
    fi
  done

  # NVM — Homebrew on macOS, official install script on Linux
  if _command_exists nvm || [ -s "$HOME/.nvm/nvm.sh" ]; then
    echo_i "nvm already installed"
  else
    echo_i "Installing nvm..."
    if [ "$OS" = "Darwin" ]; then
      brew install nvm >> "$OUTPUT_FILE" 2>&1
    else
      curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash >> "$OUTPUT_FILE" 2>&1
    fi
  fi

  # uv (Python package manager) — installer script works on both platforms
  if _command_exists uv; then
    echo_i "uv already installed"
  else
    echo_i "Installing uv..."
    if [ "$OS" = "Darwin" ]; then
      brew install uv >> "$OUTPUT_FILE" 2>&1
    else
      curl -LsSf https://astral.sh/uv/install.sh | sh >> "$OUTPUT_FILE" 2>&1
    fi
  fi

  echo_i "Dev tools installed"
}

configure_git() {
  echo_t "Configuring git"

  local current_name current_email
  current_name=$(git config --global user.name 2>/dev/null || echo "")
  current_email=$(git config --global user.email 2>/dev/null || echo "")

  read -r -p "$(printf "${BGREEN}  --> Your full name for git commits [current: '${current_name}']: ${NC}")" git_name
  git_name="${git_name:-$current_name}"

  read -r -p "$(printf "${BGREEN}  --> Your email for git commits [current: '${current_email}']: ${NC}")" git_email
  git_email="${git_email:-$current_email}"

  git config --global user.name  "$git_name"
  git config --global user.email "$git_email"

  # Sensible global defaults
  git config --global push.default        simple
  git config --global pull.rebase         false
  git config --global merge.stat          true
  git config --global core.whitespace     trailing-space,space-before-tab
  git config --global init.defaultBranch  main
  git config --global feature.manyFiles   1        # faster in large repos

  if [ "$OS" = "Darwin" ]; then
    git config --global credential.helper osxkeychain
  else
    git config --global credential.helper cache
  fi

  echo_i "Git configured for: $git_name <$git_email>"
}

setup_mac_defaults() {
  [ "$OS" != "Darwin" ] && { echo_i "Skipping macOS defaults (not macOS)"; return 0; }
  echo_t "Applying sensible macOS defaults"

  # Finder: show hidden files
  defaults write com.apple.finder AppleShowAllFiles YES

  # Finder: show path bar and status bar
  defaults write com.apple.finder ShowPathbar -bool true
  defaults write com.apple.finder ShowStatusBar -bool true

  # Keyboard: fast key repeat
  defaults write NSGlobalDomain KeyRepeat -int 2
  defaults write NSGlobalDomain InitialKeyRepeat -int 15

  # Disable .DS_Store on network drives
  defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true

  # Screenshots to ~/Desktop/Screenshots
  mkdir -p ~/Desktop/Screenshots
  defaults write com.apple.screencapture location ~/Desktop/Screenshots

  # Dock: auto-hide
  defaults write com.apple.dock autohide -bool true

  # Trackpad: tap to click
  defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true

  killall Finder 2>/dev/null || true
  killall Dock   2>/dev/null || true

  echo_i "macOS defaults applied (Finder/Dock restarted)"
}

install_node() {
  echo_t "Installing Node.js LTS (via nvm)"

  _load_nvm

  if ! _command_exists nvm; then
    echo_w "nvm not found — skipping Node install (run install_dev_tools first)"
    return 0
  fi

  if nvm ls --no-colors 2>/dev/null | grep -q "lts/\|v[0-9]"; then
    echo_i "Node already installed via nvm — skipping"
  else
    echo_i "Installing Node LTS..."
    nvm install --lts >> "$OUTPUT_FILE" 2>&1
    nvm alias default node >> "$OUTPUT_FILE" 2>&1
  fi

  echo_i "Node $(node --version 2>/dev/null || echo 'version unknown') ready"
}

install_claude_code() {
  echo_t "Installing Claude Code CLI"

  if _command_exists claude; then
    echo_i "Claude Code already installed — skipping"
    return 0
  fi

  # Ensure nvm/node is loaded
  _load_nvm

  if ! _command_exists npm; then
    echo_w "npm not found — skipping Claude Code install (run install_node first)"
    return 0
  fi

  echo_i "Installing @anthropic-ai/claude-code globally..."
  npm install -g @anthropic-ai/claude-code >> "$OUTPUT_FILE" 2>&1
  echo_i "Claude Code installed: $(claude --version 2>/dev/null || echo 'version unknown')"
}

setup_agentic_home() {
  echo_t "Setting up agentic-home"

  local repo_dir="$HOME/dev/agentic-home"

  if [ -d "$repo_dir/.git" ]; then
    echo_i "agentic-home already cloned — pulling latest..."
    git -C "$repo_dir" pull --ff-only >> "$OUTPUT_FILE" 2>&1 || echo_w "Pull failed — continuing with existing state"
  else
    mkdir -p "$HOME/dev"
    echo_i "Cloning agentic-home..."
    git clone git@github.com:ghShu/agentic-home.git "$repo_dir" >> "$OUTPUT_FILE" 2>&1
  fi

  echo_i "Running install.sh..."
  bash "$repo_dir/install.sh"
}

print_summary() {
  echo ""
  printf "${BGREEN}════════════════════════════════════════${NC}\n"
  printf "${BGREEN}  agentic-dev-setup.sh complete!${NC}\n"
  printf "${BGREEN}════════════════════════════════════════${NC}\n"
  echo ""
  echo_i "Full log: $OUTPUT_FILE"
  echo ""
  echo_ask "Next manual steps:"
  if [ "$OS" = "Darwin" ]; then
    echo "  1. Open Ghostty — set font to 'JetBrainsMono Nerd Font' if not auto-detected"
    echo "  2. Move GITHUB_TOKEN to ~/.github.env  (chmod 600 ~/.github.env)"
    echo "  3. Move ANTHROPIC_API_KEY to ~/.anthropic.env  (chmod 600 ~/.anthropic.env)"
    echo "  4. source ~/.zshrc  (or open a new terminal tab)"
    echo "  5. Run 'claude' to complete Claude Code authentication"
  else
    echo "  1. Move GITHUB_TOKEN to ~/.github.env  (chmod 600 ~/.github.env)"
    echo "  2. Move ANTHROPIC_API_KEY to ~/.anthropic.env  (chmod 600 ~/.anthropic.env)"
    echo "  3. source ~/.zshrc  (or open a new terminal tab)"
    echo "  4. Run 'claude' to complete Claude Code authentication"
  fi
}

# ─── Orchestration ────────────────────────────────────────────────────────────

STEPS=(
  check_prereqs
  fix_ssh_permissions
  setup_package_manager
  install_terminal
  install_nerd_font
  setup_shell
  write_zshrc
  install_dev_tools
  configure_git
  setup_mac_defaults
  install_node
  install_claude_code
  setup_agentic_home
)

run_all() {
  for step in "${STEPS[@]}"; do
    "$step"
  done
  print_summary
}

run_from() {
  local target="$1"
  local found=false
  for step in "${STEPS[@]}"; do
    if [ "$step" = "$target" ]; then found=true; fi
    if $found; then "$step"; fi
  done
  if ! $found; then
    echo_e "Step '$target' not found. Available steps:"
    printf '  %s\n' "${STEPS[@]}"
    exit 1
  fi
  print_summary
}

print_help() {
  echo ""
  echo "agentic-dev-setup.sh v$VERSION — Agentic dev environment setup (macOS + Linux)"
  echo ""
  echo "Usage:"
  echo "  ./agentic-dev-setup.sh              Run all steps"
  echo "  ./agentic-dev-setup.sh --from STEP  Resume from a specific step"
  echo "  ./agentic-dev-setup.sh STEP [STEP]  Run one or more specific steps"
  echo "  ./agentic-dev-setup.sh --help       Show this help"
  echo ""
  echo "Available steps:"
  printf '  %s\n' "${STEPS[@]}"
  echo ""
}

main() {
  printf "${BGREEN}agentic-dev-setup.sh v${VERSION} [%s]${NC}\n" "$OS"
  printf "${BROWN}Full log: $OUTPUT_FILE${NC}\n\n"

  case "${1:-}" in
    --help|-h)   print_help; exit 0 ;;
    --version|-v) echo "$VERSION"; exit 0 ;;
    --from)
      if [ -z "${2:-}" ]; then
        echo_e "--from requires a step name"
        print_help; exit 1
      fi
      run_from "$2"
      ;;
    "")
      if _confirm_choice "Fresh install? Run full setup (package manager, terminal, dev tools, shell config)"; then
        run_all
      else
        echo_i "Skipping full setup — installing Node, Claude Code, and agentic-home only..."
        install_node
        install_claude_code
        setup_agentic_home
        print_summary
      fi
      ;;
    *)
      # Run explicitly named steps
      for step in "$@"; do
        if [[ "$step" == -* ]]; then continue; fi
        if declare -f "$step" > /dev/null; then
          "$step"
        else
          echo_e "Unknown step: $step"
          print_help; exit 1
        fi
      done
      ;;
  esac
}

main "$@"
