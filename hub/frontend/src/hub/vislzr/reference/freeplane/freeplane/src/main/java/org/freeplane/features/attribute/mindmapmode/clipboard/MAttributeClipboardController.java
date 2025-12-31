package org.freeplane.features.attribute.mindmapmode.clipboard;

import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.awt.event.ActionEvent;
import java.io.IOException;
import java.io.StringReader;
import java.util.ArrayList;
import java.util.List;

import javax.swing.JTable;

import org.freeplane.core.io.xml.XMLLocalParserFactory;
import org.freeplane.core.util.TypeReference;
import org.freeplane.features.attribute.Attribute;
import org.freeplane.features.attribute.AttributeController;
import org.freeplane.features.attribute.AttributeSelection;
import org.freeplane.features.attribute.AttributeSelection.SelectedAttribute;
import org.freeplane.features.attribute.IAttributeTableModel;
import org.freeplane.features.attribute.NodeAttribute;
import org.freeplane.features.attribute.NodeAttributeTableModel;
import org.freeplane.features.attribute.clipboard.AttributeClipboardController;
import org.freeplane.features.attribute.clipboard.AttributeTransferable;
import org.freeplane.features.attribute.mindmapmode.MAttributeController;
import org.freeplane.features.clipboard.mindmapmode.MClipboardController;
import org.freeplane.features.map.NodeModel;
import org.freeplane.features.mode.Controller;
import org.freeplane.n3.nanoxml.IXMLParser;
import org.freeplane.n3.nanoxml.IXMLReader;
import org.freeplane.n3.nanoxml.StdXMLReader;
import org.freeplane.n3.nanoxml.XMLElement;
import org.freeplane.n3.nanoxml.XMLException;

public class MAttributeClipboardController
extends AttributeClipboardController implements MClipboardController{
	private final MAttributeController attributeController;

	public MAttributeClipboardController(MAttributeController attributeController) {
		this.attributeController = attributeController;
	}
	@Override
	public boolean canPaste(Transferable t) {
		return t.isDataFlavorSupported(AttributeTransferable.attributesFlavor);
	}

	@Override
	public void paste(ActionEvent event, Transferable t) {
		try {
			final AttributeSelection selection = AttributeController.getAttributeSelection();
			final NodeModel target = Controller.getCurrentController().getSelection().getSelected();

			if (selection != null && !selection.isEmpty()) {
				final List<SelectedAttribute> selectedAttributes = selection.getSelectedAttributes();
				if (selectedAttributes.size() == 1 && selectedAttributes.get(0).getSelectedPart() != SelectedAttribute.SelectedPart.BOTH) {
					final SelectedAttribute selected = selectedAttributes.get(0);
					final NodeAttribute nodeAttribute = selected.getSelectedAttribute();
					final NodeModel node = nodeAttribute.node;
					final NodeAttributeTableModel model = node.getExtension(NodeAttributeTableModel.class);
					final int row = model.getAttributeIndex(nodeAttribute.attribute);
					final int col = selected.getSelectedPart() == SelectedAttribute.SelectedPart.NAME ? 0 : 1;
					Object stringContent = t.getTransferData(DataFlavor.stringFlavor);
					attributeController.performSetValueAt(node, model, stringContent, row, col);
					return;
				}

				final String transferData = (String) t.getTransferData(AttributeTransferable.attributesFlavor);
				final IXMLParser parser = XMLLocalParserFactory.createLocalXMLParser();
				final IXMLReader xmlReader = new StdXMLReader(new StringReader(transferData));
				parser.setReader(xmlReader);
				final List<Attribute> clipboardAttributes = new ArrayList<>();
				while (!xmlReader.atEOF()) {
					final XMLElement storage = (XMLElement) parser.parse();
					final String name = storage.getAttribute("name", null);
					final String object = storage.getAttribute("object", null);
					final Object value = TypeReference.create(object);
					clipboardAttributes.add(new Attribute(name, value));
				}

				if (clipboardAttributes.isEmpty()) {
					return;
				}

				for (int i = 0; i < selectedAttributes.size(); i++) {
					final SelectedAttribute sel = selectedAttributes.get(i);
					final Attribute sourceAttr = clipboardAttributes.get(Math.min(i, clipboardAttributes.size() - 1));
					final NodeAttribute nodeAttr = sel.getSelectedAttribute();
					final NodeModel node = nodeAttr.node;
					final NodeAttributeTableModel model = node.getExtension(NodeAttributeTableModel.class);
					final int row = model.getAttributeIndex(nodeAttr.attribute);
					switch (sel.getSelectedPart()) {
						case NAME:
							attributeController.performSetValueAt(node, model, sourceAttr.getName(), row, 0);
							break;
						case VALUE:
							attributeController.performSetValueAt(node, model, sourceAttr.getValue(), row, 1);
							break;
						case BOTH:
							attributeController.setAttribute(node, row, new Attribute(sourceAttr.getName(), sourceAttr.getValue()));
							break;
						default:
							break;
					}
				}
				return;
			}

			final String transferData = (String) t.getTransferData(AttributeTransferable.attributesFlavor);
			final IXMLParser parser = XMLLocalParserFactory.createLocalXMLParser();
			final IXMLReader xmlReader = new StdXMLReader(new StringReader(transferData));
			parser.setReader(xmlReader);
			int targetRow = targetRow(event);
			while (!xmlReader.atEOF()) {
				final XMLElement storage = (XMLElement) parser.parse();
				String name = storage.getAttribute("name", null);
				final String object = storage.getAttribute("object", null);
				Object value = TypeReference.create(object);
				Attribute attribute = new Attribute(name, value);
				if (targetRow >= 0)
					attributeController.insertAttribute(target, targetRow++, attribute);
				else
					attributeController.addAttribute(target, attribute);
			}
		}
		catch (UnsupportedFlavorException | IOException | XMLException e) {
			throw new IllegalArgumentException(e);
		}
	}
	private int targetRow(ActionEvent event) {
		if(event.getSource() instanceof JTable) {
			JTable table = (JTable) event.getSource();
			if (table.getModel() instanceof IAttributeTableModel) {
				final int targetRow;
				IAttributeTableModel model = (IAttributeTableModel) table.getModel();
				int selectedRowCount = table.getSelectedRowCount();
				if(selectedRowCount != 0) {
					int[] selectedRows = table.getSelectedRows();
					targetRow = model.targetRow(selectedRows[selectedRows.length - 1]) +1;
				}
				else
					targetRow = 0;
				return targetRow;
			}
		}
		return -1;
	}

	@Override
	public boolean canCut() {
		return canCopy();
	}

	@Override
	public void cut() {
		copy();
		final AttributeSelection attributeSelection = AttributeController.getAttributeSelection();
		attributeSelection.nodeAttributeStream().forEach(this::delete);

	}

	private void delete(NodeAttribute nodeAttribute) {
		final NodeModel node = nodeAttribute.node;
		final NodeAttributeTableModel model = node.getExtension(NodeAttributeTableModel.class);
		final int attributeIndex = model.getAttributeIndex(nodeAttribute.attribute);
		attributeController.performRemoveRow(node, model, attributeIndex);

	}
}
