package com.bughunter.arjunconverter;

import burp.api.montoya.BurpExtension;
import burp.api.montoya.MontoyaApi;

public class BurpExtender implements BurpExtension
{
    @Override
    public void initialize(MontoyaApi api)
    {
        // Set the name of the extension
        api.extension().setName("Arjun Converter (Montoya)");

        // Register the custom context menu factory
        api.userInterface().registerContextMenuItemsProvider(new ArjunContextMenuItemsProvider(api));

        // Log a successful load message to the Extender Output
        api.logging().logToOutput("Arjun Converter (Montoya) Extension loaded successfully.");
    }
}