(function () {

    const processDataBridge = function (data) {
        let actionsPerformed = 0;
        let updateNeeded = false;

        if (data.replacedPlaceholder) {
            updateNeeded |= CMS.API.StructureBoard.handleClearPlaceholder(data.replacedPlaceholder);
            actionsPerformed++;
        }
        if (data.replacedPlugin) {
            updateNeeded |= CMS.API.StructureBoard.handleDeletePlugin(data.replacedPlugin);
            actionsPerformed++;
        }
        if (data.addedPlugins) {
            for (const addedPlugin of data.addedPlugins) {
                updateNeeded |= CMS.API.StructureBoard.handleAddPlugin(addedPlugin);
                actionsPerformed++;
            }
        }
        if (data.movedPlugins) {
            for (const movedPlugin of data.movedPlugins) {
                updateNeeded |= CMS.API.StructureBoard.handleMovePlugin(movedPlugin);
                actionsPerformed++;
            }
        }

        if (updateNeeded) {
            CMS.API.StructureBoard._requestcontent = null;
            CMS.API.StructureBoard.updateContent();
        }
        return actionsPerformed;
    }

    const iframe = window.parent.document.querySelector('.cms-modal-frame > iframe');
    const {CMS} = window.parent;

    if (!iframe || !CMS) {
        return;
    }

    // Register the event handler in the capture phase to increase the chance it runs first
    iframe.addEventListener('load', function (event) {
        const iframeDocument = iframe.contentDocument || iframe.contentWindow.document;
        const dataBridge = iframeDocument.body.querySelector('script#data-bridge');
        if (dataBridge) {
            try {
                const data = JSON.parse(dataBridge.textContent);
                if (data.action === 'ALIAS_REPLACE') {
                    event.stopPropagation();
                    dataBridge.parentNode.removeChild(dataBridge);
                    if (processDataBridge(data)) {
                    }
                    iframe.dispatchEvent(new Event('load')); // re-dispatch load event to trigger modal close
                }
            } catch (error) {
                window.parent.console.error('Error parsing data bridge script:', error);
            }
            iframeDocument.body.textContent = JSON.stringify(dataBridge);
        }
    }, true); // 'true' sets the event to be handled in the capture phase before the modals handler
})();