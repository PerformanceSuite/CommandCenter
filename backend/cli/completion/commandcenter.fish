# Fish completion script for commandcenter CLI

function _commandcenter_completion
    set -l response (env _COMMANDCENTER_COMPLETE=fish_complete COMP_WORDS=(commandline -opc) COMP_CWORD=(count (commandline -opc)) commandcenter)

    for completion in $response
        set -l metadata (string split "," $completion)

        if test $metadata[1] = "dir"
            __fish_complete_directories $metadata[2]
        else if test $metadata[1] = "file"
            __fish_complete_path $metadata[2]
        else if test $metadata[1] = "plain"
            echo $metadata[2]
        end
    end
end

complete -c commandcenter -f -a "(_commandcenter_completion)"
