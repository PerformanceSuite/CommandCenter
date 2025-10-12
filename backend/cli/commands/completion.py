"""
Shell completion commands for CommandCenter CLI.

Generates completion scripts for bash, zsh, and fish shells.
"""

import click


@click.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completion(shell):
    """
    Generate shell completion script.

    Examples:
        # Bash
        eval "$(commandcenter completion bash)"

        # Zsh
        eval "$(commandcenter completion zsh)"

        # Fish
        commandcenter completion fish | source
    """
    if shell == "bash":
        script = """
_commandcenter_completion() {
    local IFS=$'\\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" \\
                   COMP_CWORD=$COMP_CWORD \\
                   _COMMANDCENTER_COMPLETE=bash_complete $1)

    for completion in $response; do
        IFS=',' read type value <<< "$completion"

        if [[ $type == 'dir' ]]; then
            COMPREPLY=()
            compopt -o dirnames
        elif [[ $type == 'file' ]]; then
            COMPREPLY=()
            compopt -o default
        elif [[ $type == 'plain' ]]; then
            COMPREPLY+=($value)
        fi
    done

    return 0
}

complete -o nosort -F _commandcenter_completion commandcenter
"""
    elif shell == "zsh":
        script = """
#compdef commandcenter

_commandcenter() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[commandcenter] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" \\
                       COMP_CWORD=$((CURRENT-1)) \\
                       _COMMANDCENTER_COMPLETE=zsh_complete commandcenter)}")

    for type_value in "${response[@]}"; do
        _type="${type_value%%,*}"
        _value="${type_value#*,}"

        if [[ "$_type" == "dir" ]]; then
            _path_files -/
        elif [[ "$_type" == "file" ]]; then
            _path_files -f
        elif [[ "$_type" == "plain" ]]; then
            if [[ "$_value" == *$'\\t'* ]]; then
                completions_with_descriptions+=("$_value")
            else
                completions+=("$_value")
            fi
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi
}

if [[ "$(basename -- ${(%):-%x})" != "_commandcenter" ]]; then
    compdef _commandcenter commandcenter
fi
"""
    else:  # fish
        script = """
function _commandcenter_completion
    set -l response (env _COMMANDCENTER_COMPLETE=fish_complete COMP_WORDS=(commandline -opc) \\
                         COMP_CWORD=(count (commandline -opc)) commandcenter)

    for completion in $response
        set -l metadata (string split "," -- $completion)

        if test $metadata[1] = "dir"
            __fish_complete_directories $metadata[2]
        else if test $metadata[1] = "file"
            __fish_complete_path $metadata[2]
        else if test $metadata[1] = "plain"
            echo $metadata[2]
        end
    end
end

complete --no-files --command commandcenter --arguments '(_commandcenter_completion)'
"""

    click.echo(script)
