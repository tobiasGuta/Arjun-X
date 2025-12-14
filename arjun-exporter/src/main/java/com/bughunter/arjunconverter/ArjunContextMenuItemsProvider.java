package com.bughunter.arjunconverter;

import burp.api.montoya.MontoyaApi;
import burp.api.montoya.http.message.HttpRequestResponse;
import burp.api.montoya.http.message.requests.HttpRequest;
import burp.api.montoya.ui.contextmenu.ContextMenuEvent;
import burp.api.montoya.ui.contextmenu.ContextMenuItemsProvider;

import java.awt.Component;
import java.awt.Toolkit;
import java.awt.datatransfer.Clipboard;
import java.awt.datatransfer.StringSelection;
import java.util.List;
import java.util.stream.Collectors;
import javax.swing.JMenuItem;

public class ArjunContextMenuItemsProvider implements ContextMenuItemsProvider
{
    private final MontoyaApi api;

    public ArjunContextMenuItemsProvider(MontoyaApi api)
    {
        this.api = api;
    }

    @Override
    public List<Component> provideMenuItems(ContextMenuEvent event)
    {
        List<HttpRequestResponse> selectedMessagesList = event.selectedRequestResponses();

        if (selectedMessagesList != null && !selectedMessagesList.isEmpty())
        {
            JMenuItem arjunItem = new JMenuItem("Convert to Arjun Command & Copy");

            arjunItem.addActionListener(actionEvent -> {

                HttpRequestResponse httpTraffic = selectedMessagesList.get(0);

                String arjunCommand = generateArjunCommand(httpTraffic.request());

                api.logging().logToOutput("--- Generated Arjun Command ---");
                api.logging().logToOutput(arjunCommand);
                api.logging().logToOutput("-----------------------------");

                copyToClipboard(arjunCommand);
                api.logging().logToOutput("Command copied to clipboard.");

                api.logging().logToOutput("ALERT: Arjun command copied to clipboard!");
            });

            return List.of(arjunItem);
        }

        return List.of();
    }

    /**
     * Extracts details from the HTTP request and formats the arjun command
     * to match the requested multi-line, configured format.
     */
    private String generateArjunCommand(HttpRequest request)
    {
        // Headers to exclude from the --headers argument (case-insensitive)
        List<String> excludedHeaders = List.of("Host", "Content-Length", "Connection", "Priority", "Accept-Encoding");

        // 1. Build the clean header string
        String headerString = request.headers().stream()
                .filter(header -> !header.name().isEmpty())
                .filter(header -> !excludedHeaders.stream().anyMatch(h -> h.equalsIgnoreCase(header.name())))
                .map(header -> header.name() + ": " + header.value())
                .collect(Collectors.joining("\n"));

        // 2. Escape the Java newline '\n' to be the literal sequence '\n' in the shell string ($'...')
        String escapedHeaderString = headerString.trim().replace("\n", "\\n");

        // 3. Assemble the final multi-line command string
        String arjunCommand = String.format(
                "arjun \\%n" +
                        "  -u %s \\%n" +
                        "  -m JSON \\%n" +
                        "  --stable \\%n" +
                        "  --rate-limit 5 \\%n" +
                        "  --stealth \\%n" +
                        "  --headers $'%s'",
                "\"" + request.url() + "\"", // URL enclosed in quotes
                escapedHeaderString
        );

        return arjunCommand;
    }

    /**
     * Utility function to copy the resulting command to the system clipboard.
     */
    private void copyToClipboard(String text) {
        StringSelection stringSelection = new StringSelection(text);
        Clipboard clipboard = Toolkit.getDefaultToolkit().getSystemClipboard();
        clipboard.setContents(stringSelection, null);
    }
}