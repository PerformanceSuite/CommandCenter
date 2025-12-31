package org.freeplane.core.util;

import java.util.function.Supplier;

public class SupplierRule<T, R extends Enum<?>> implements ObjectRule<T, R> {
	final private Supplier<T> supplier;

	public SupplierRule(Supplier<T> supplier) {
		this.supplier = supplier;
	}

	@Override
	public T getValue() {
		return supplier.get();
	}

	@Override
	public boolean hasValue() {
		return true;
	}

	@Override
	public void resetCache() {
	}

	@Override
	public R getRule() {
		return null;
	}

	@Override
	public void setCache(T value) {
	}
}
